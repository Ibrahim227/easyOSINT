document.querySelector('.filter-button').addEventListener('click', function() {
    this.parentElement.classList.toggle('show-dropdown');
});

const dropdownOptions = document.querySelectorAll('.dropdown-option');
dropdownOptions.forEach(option => {
    option.addEventListener('click', function() {
        console.log('Filter by:', this.getAttribute('data-value'));
        document.querySelector('.filter-button').innerHTML = '<i class="fas fa-filter"></i> Filter by ' + ':' + ' ' + this.innerText;
        document.querySelector('.filter-container').classList.remove('show-dropdown');
    });
});
