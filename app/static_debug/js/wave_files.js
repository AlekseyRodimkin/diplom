const input = document.getElementById("documents");
const preview = document.getElementById("preview");

let filesList = [];

input.addEventListener("change", function (e) {
    for (let f of Array.from(e.target.files)) {
        filesList.push(f);
    }

    if (filesList.length > 15) {
        alert("Можно загрузить не более 15 файлов.");
        filesList = filesList.slice(0, 15);
    }

    updatePreview();
});

function updatePreview() {
    preview.innerHTML = "";

    filesList.forEach((file, index) => {
        const row = document.createElement("div");
        row.className = "d-flex align-items-center mb-2";

        row.innerHTML = `
            <span class="me-2">${truncateName(file.name)}</span>
            <button type="button" class="btn btn-sm btn-danger">✕</button>
        `;

        row.querySelector("button").onclick = () => {
            removeFile(index);
        };

        preview.appendChild(row);
    });

    updateInputFiles();
}

function truncateName(name, limit = 40) {
    if (name.length <= limit) return name;
    return name.slice(0, limit - 3) + "...";
}

function removeFile(index) {
    filesList.splice(index, 1);
    updatePreview();
}

function updateInputFiles() {
    const dataTransfer = new DataTransfer();
    filesList.forEach(f => dataTransfer.items.add(f));
    input.files = dataTransfer.files;
}
