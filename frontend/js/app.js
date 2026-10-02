const studentPermissions = JSON.parse(
  document.querySelector("#studentPermissions").textContent
);
const searchInput = document.querySelector("#studentSearch");
const searchSummary = document.querySelector("#searchSummary");
const studentFormError = document.querySelector("#studentFormError");
const studentDialogTitle = document.querySelector("#studentDialogTitle");
const saveStudentButton = document.querySelector("#saveStudentButton");

let editingRow = null;

function filterStudents() {
  const studentRows = document.querySelectorAll("#studentTableBody tr");
  const query = searchInput.value.trim().toLowerCase();
  let visibleCount = 0;

  studentRows.forEach((row) => {
    const searchableValues = [
      row.cells[0].textContent, // Student number
      row.cells[1].textContent, // Name
      row.cells[2].textContent, // Email
    ];

    const matches = searchableValues.some((value) =>
      value.toLowerCase().includes(query)
    );

    row.hidden = !matches;

    if (matches) {
      visibleCount += 1;
    }
  });

  searchSummary.textContent =
    visibleCount === 0
      ? "No students found. Try another name, email, or student number."
      : `Showing ${visibleCount} of ${studentRows.length} students.`;
}

searchInput.addEventListener("input", filterStudents);

filterStudents();

const studentDialog = document.querySelector("#studentDialog");
const studentForm = document.querySelector("#studentForm");
const addStudentButton = document.querySelector("#addStudentButton");
addStudentButton.hidden = !studentPermissions.can_add;
const cancelStudentButton = document.querySelector("#cancelStudentButton");

addStudentButton.addEventListener("click", () => {
  editingRow = null;
  studentForm.reset();
  studentFormError.textContent = "";
  studentDialogTitle.textContent = "Add Student";
  saveStudentButton.textContent = "Save Student";
  studentDialog.showModal();
});

cancelStudentButton.addEventListener("click", ()=>
{
  studentDialog.close();
});
// Prevent Escape from closing the dialog while saving.
studentDialog.addEventListener("cancel", (event) => {
  if (saveStudentButton.disabled) {
    event.preventDefault();
  }
});
// Prevent page navigation while saving is not implemented.
studentForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (saveStudentButton.disabled) {
    return;
  }

  studentFormError.textContent = "";

  const formData = new FormData(studentForm);
  const payload = new FormData();

  payload.set("student_number", formData.get("sNumber").trim());
  payload.set("full_name", formData.get("sFullName").trim());
  payload.set("email", formData.get("sEmail").trim());
  payload.set("department", formData.get("sDepartment").trim());
  payload.set(
    "is_active",
    formData.get("sStatus") === "1" ? "true" : "false"
  );

  const requiredFields = [
    "student_number",
    "full_name",
    "email",
    "department",
  ];

  if (requiredFields.some((field) => !payload.get(field))) {
    studentFormError.textContent =
      "Please fill in every field. Spaces alone are not valid.";
    return;
  }
//------------------//
  const rowBeingEdited = editingRow;
  const submitLabel = rowBeingEdited ? "Save Changes" : "Save Student";

  const url = rowBeingEdited
    ? `/api/students/${rowBeingEdited.dataset.id}/update/`
    : "/api/students/create/";
//------------------//
  saveStudentButton.disabled = true;
  cancelStudentButton.disabled = true;
  saveStudentButton.textContent = "Saving...";

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
      },
      body: payload,
    });

    const isJson = response.headers
      .get("content-type")
      ?.includes("application/json");

    if (!isJson) {
      throw new Error(
        "Unexpected server response. Reload the page and sign in again if needed."
      );
    }

    const data = await response.json();

    if (!response.ok) {
      const messages = Object.values(data.errors ?? {})
        .flat()
        .map((error) => error.message);

      throw new Error(
        messages.join(" ") ||
          data.error ||
          "Unable to save the student."
      );
    }

    const student = data.student;

    const savedStudent = {
      id: student.id,
      studentNumber: student.student_number,
      fullName: student.full_name,
      email: student.email,
      department: student.department,
      status: student.is_active ? "1" : "0",
    };

    if (rowBeingEdited) {
      updateStudentRow(rowBeingEdited, savedStudent);
    } else {
      addStudentRow(savedStudent);
    }

    filterStudents();
    studentDialog.close();
  } catch (error) {
    studentFormError.textContent =
      error instanceof TypeError
        ? "Could not confirm the save. Check your connection and reload before retrying."
        : error.message;
  } finally {
    saveStudentButton.disabled = false;
    cancelStudentButton.disabled = false;
    saveStudentButton.textContent = submitLabel;
  }
});

function addStudentRow(student) {
  const row = document.createElement("tr");

  [
    student.studentNumber,
    student.fullName,
    student.email,
    student.department,
  ].forEach((value) => {
    const cell = document.createElement("td");
    cell.textContent = value;
    row.appendChild(cell);
  });

  const statusCell = document.createElement("td");
  const badge = document.createElement("span");
  const isActive = student.status === "1";

  badge.className = `status ${isActive ? "active" : "inactive"}`;
  badge.textContent = isActive ? "Active" : "Inactive";
  statusCell.appendChild(badge);
  row.appendChild(statusCell);

  const actionsCell = document.createElement("td");
  actionsCell.className = "student-actions";

  const actions = ["View"];

  if (studentPermissions.can_change) {
    actions.push("Edit");
  }

  if (studentPermissions.can_delete) {
    actions.push("Delete");
  }

  actions.forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = action.toLowerCase();
    button.textContent = action;
    actionsCell.appendChild(button);
  });

  row.appendChild(actionsCell);
  row.dataset.id = student.id;
  document.querySelector("#studentTableBody").appendChild(row);
}
const studentTableBody = document.querySelector("#studentTableBody");

studentTableBody.addEventListener("click", async (event) => {
  const deleteButton = event.target.closest("button.delete");

  if (!deleteButton || deleteButton.disabled) {
    return;
  }

  const row = deleteButton.closest("tr");
  const studentName = row.cells[1].textContent;

  if (!window.confirm(`Delete the record for ${studentName}?`)) {
    return;
  }

  const buttons = row.querySelectorAll("button");
  buttons.forEach((button) => {
    button.disabled = true;
  });
  deleteButton.textContent = "Deleting...";

  try {
    const csrfToken = studentForm.elements.namedItem(
      "csrfmiddlewaretoken"
    ).value;

    const response = await fetch(
      `/api/students/${row.dataset.id}/delete/`,
      {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
      }
    );

    const isJson = response.headers
      .get("content-type")
      ?.includes("application/json");

    if (!isJson) {
      throw new Error(
        "Unexpected server response. Reload the page and sign in again if needed."
      );
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.error || "Unable to delete the student."
      );
    }

    row.remove();
    filterStudents();
  } catch (error) {
    window.alert(
      error instanceof TypeError
        ? "Could not confirm deletion. Check your connection and reload before retrying."
        : error.message
    );
  } finally {
    buttons.forEach((button) => {
      button.disabled = false;
    });
    deleteButton.textContent = "Delete";
  }
});
const studentDetailsDialog = document.querySelector("#studentDetailsDialog");
const closeDetailsButton = document.querySelector("#closeDetailsButton");

studentTableBody.addEventListener("click", (event) => {
  const viewButton = event.target.closest("button.view");

  if (!viewButton) {
    return;
  }

  const row = viewButton.closest("tr");

  document.querySelector("#detailNumber").textContent =
    row.cells[0].textContent.trim();
  document.querySelector("#detailName").textContent =
    row.cells[1].textContent.trim();
  document.querySelector("#detailEmail").textContent =
    row.cells[2].textContent.trim();
  document.querySelector("#detailDepartment").textContent =
    row.cells[3].textContent.trim();
  document.querySelector("#detailStatus").textContent =
    row.cells[4].textContent.trim();

  studentDetailsDialog.showModal();
});

closeDetailsButton.addEventListener("click", () => {
  studentDetailsDialog.close();
});
studentTableBody.addEventListener("click", (event) => {
  const editButton = event.target.closest("button.edit");

  if (!editButton) {
    return;
  }

  editingRow = editButton.closest("tr");
  studentForm.reset();
  studentFormError.textContent = "";

  studentForm.elements.namedItem("sNumber").value =
    editingRow.cells[0].textContent.trim();
  studentForm.elements.namedItem("sFullName").value =
    editingRow.cells[1].textContent.trim();
  studentForm.elements.namedItem("sEmail").value =
    editingRow.cells[2].textContent.trim();
  studentForm.elements.namedItem("sDepartment").value =
    editingRow.cells[3].textContent.trim();
  studentForm.elements.namedItem("sStatus").value =
    editingRow.cells[4].querySelector(".status").classList.contains("active")
      ? "1"
      : "0";

  studentDialogTitle.textContent = "Edit Student";
  saveStudentButton.textContent = "Save Changes";
  studentDialog.showModal();
});

studentDialog.addEventListener("close", () => {
  editingRow = null;
});

function updateStudentRow(row, student) {
  row.cells[0].textContent = student.studentNumber;
  row.cells[1].textContent = student.fullName;
  row.cells[2].textContent = student.email;
  row.cells[3].textContent = student.department;

  const badge = row.cells[4].querySelector(".status");
  const isActive = student.status === "1";

  badge.className = `status ${isActive ? "active" : "inactive"}`;
  badge.textContent = isActive ? "Active" : "Inactive";
}
//----//
async function loadStudents() {
  searchSummary.textContent = "Loading students...";
  searchInput.disabled = true;

  try {
    const response = await fetch("/api/students/");

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("Your session has expired. Reload the page to sign in.");
      }

      if (response.status === 403) {
        throw new Error("You do not have permission to view students.");
      }

      throw new Error("Unable to load students. Please reload to try again.");
    }

    const data = await response.json();

    studentTableBody.replaceChildren();

    data.students.forEach((student) => {
      addStudentRow({
        id: student.id,
        studentNumber: student.student_number,
        fullName: student.full_name,
        email: student.email,
        department: student.department,
        status: student.is_active ? "1" : "0",
      });
    });

    searchInput.disabled = false;
    filterStudents();
    addStudentButton.disabled = !studentPermissions.can_add;
  } 
  catch (error) {
    searchSummary.textContent = error.message;
  }
}

loadStudents();