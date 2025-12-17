document.querySelectorAll('.change-status').forEach(select => {
    select.addEventListener('change', () => {
        const status = select.value;
        const id = select.dataset.id;

        if (!confirm(`Вы уверены, что хотите изменить статус на "${status}"?`)) {
            select.value = select.dataset.previous || select.value;
            return;
        }
        select.dataset.previous = status;

        const form = document.getElementById(`status-form-${id}`);
        form.querySelector('input[name="status"]').value = status;
        form.submit();
    });
});
