document.querySelectorAll('.show-items').forEach(btn => {
    btn.addEventListener('click', () => {
        const inboundId = btn.dataset.inboundId;
        const tbody = document.getElementById('items-table-body');
        tbody.innerHTML = '<tr><td colspan="4">Загрузка…</td></tr>';

        fetch(btn.dataset.url)
            .then(r => r.json())
            .then(data => {
                tbody.innerHTML = '';
                data.forEach(row => {
                    tbody.insertAdjacentHTML('beforeend', `
                        <tr>
                            <td>${row.item_code}</td>
                            <td>${row.qty}</td>
                            <td>${row.weight}</td>
                            <td>${row.description}</td>
                        </tr>
                    `);
                });
            });

        new bootstrap.Modal(document.getElementById('itemsModal')).show();
    });
});