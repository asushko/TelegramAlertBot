document.querySelectorAll('tr.low, tr.high').forEach(row => {
    if (row.querySelector('td:nth-child(4)').textContent >= row.querySelector('td:nth-child(2)').textContent) {
        row.classList.remove('low', 'high');
    }
});
