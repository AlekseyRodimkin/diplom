const inbInput = document.getElementById("inb_form");

inbInput.addEventListener("change", function (e) {
    const file = e.target.files[0];

    if (!file) return;

    if (file.name !== "INB-FORM.xlsx") {
        alert("Имя файла должно быть INB-FORM.xlsx");
        inbInput.value = "";
    }
});
