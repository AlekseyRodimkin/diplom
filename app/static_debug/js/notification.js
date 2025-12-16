setTimeout(() => {
    const alerts = document.querySelectorAll('#flash-messages .alert');
    alerts.forEach(a => {
        a.classList.remove('show');
        a.classList.add('fade');
        setTimeout(() => a.remove(), 500);
    });
}, 8000); // 8 секунд
