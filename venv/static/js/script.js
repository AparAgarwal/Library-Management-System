// static/js/script.js

document.addEventListener('DOMContentLoaded', function () {
    console.log('Script loaded!');

    // Example: Add a click event to a button with the ID "myButton"
    var myButton = document.getElementById('myButton');
    if (myButton) {
        myButton.addEventListener('click', function () {
            alert('Button clicked!');
        });
    }
});

//Issue Book function...
function issueBook(isbn) {
    fetch(`/issue_book/${isbn}`, { method: 'POST' })
        .then(response => {
            console.log('Response:', response);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Book issued successfully!');
                location.reload();
            } else {
                if (data.message.includes('already issued')) {
                    alert('Book already issued. You cannot issue multiple copies.');
                } else if (data.message.includes('maximum limit')) {
                    alert('You have reached the maximum limit of issued books. Please return some books first.');
                } else {
                    alert('Failed to issue the book. Please try again.');
                }
            }
        })
        .catch(error => {
            console.error('Error issuing book:', error);
            alert('An error occurred. Please try again.');
        });
}

function returnBook(isbn) {
    fetch(`/return_book/${isbn}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Book returned successfully!');
                location.reload();
            } else {
                alert('Failed to return the book. ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error returning book:', error);
            alert('An error occurred. Please try again.');
        });
}