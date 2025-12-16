const inbInput = document.getElementById("out_form");

inbInput.addEventListener("change", function (e) {
    const file = e.target.files[0];

    if (!file) return;

    if (file.name !== "OUT-FORM.xlsx") {
        alert("Имя файла должно быть OUT-FORM.xlsx");
        inbInput.value = "";
    }
});
