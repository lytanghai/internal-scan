function displayResultCount(count) {
    console.log("display res " + count);
    const resultLabel = document.getElementById("on_filtered_result");
    if (!resultLabel) {
        console.error("Element with id 'on_filtered_result' not found.");
        return;
    }

    if (count === 0) {
        resultLabel.textContent = "No results found!";
    } else {
        resultLabel.innerHTML = `<span style="color:brown">${count}</span> results found!`;
    }
}

// Loading
function showLoader() {
    document.getElementById("loading-overlay").style.display = "flex";
}

function hideLoader() {
    document.getElementById("loading-overlay").style.display = "none";
}

function renderWorkspaceList() {
    const list = document.getElementById("workspace-list");
    list.innerHTML = ""; // Clear old list

    workspaces.forEach((ws, index) => {
        const li = document.createElement("li");
        li.textContent = ws;

        const deleteBtn = document.createElement("button");
        deleteBtn.textContent = "🗑️";
        deleteBtn.className = "delete-btn";

        deleteBtn.onclick = (e) => {
            e.preventDefault();

            createWorkspace(ws, 'delete', (data) => {
                alert("Workspace deleted successfully!");
                workspaces.splice(index, 1);
                renderWorkspaceList(); // Refresh list

                // Optionally remove it from the dropdown too
                const select = document.getElementById("workspace");
                [...select.options].forEach((opt) => {
                    if (opt.value === ws) select.removeChild(opt);
                });
            });
        };

        li.appendChild(deleteBtn);
        list.appendChild(li);
    });
}

  document.getElementById("open_panel_btn").addEventListener("click", function () {
    const panel = document.getElementById("panel");

    if (panel.style.display === "block") {
        panel.style.display = "none";
    } else {
        panel.style.display = "block";
        renderWorkspaceList(); // Only refresh list when opening
    }
});

// Close the panel when clicking the close button
if (document.getElementById("close_panel_btn") !== null) {
    document.getElementById("close_panel_btn").addEventListener("click", function() {
        const panel = document.querySelector(".hidden-panel");
        panel.style.display = "none";
    });
}
document.getElementById("open_workspace_panel_btn").addEventListener("click", () => {
    const panel = document.getElementById("panel");
    panel.style.display = panel.style.display === "block" ? "none" : "block";
    renderWorkspaceList();
  });
  

  
//   document.getElementById("apply_filter").addEventListener("click", function () {
//     // Prepare your requestBody here...
  
//     showLoader();
  
//     fetch('/pull_request/api/filter', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(requestBody)
//     })
//       .then(response => response.json())
//       .then(data => {
//         hideLoader();
//         console.log("Fetched data:", data);
//         // update table here...
//       })
//       .catch(error => {
//         hideLoader();
//         console.error("Fetch error:", error);
//       });
//   });
  
