
// Main JavaScript for Sentinel AI Platform

document.addEventListener('DOMContentLoaded', function() {
    // Event listener for analysis type change in analyze.html
    const analysisTypeSelect = document.getElementById('analysis_type');
    if (analysisTypeSelect) {
        analysisTypeSelect.addEventListener('change', function() {
            const analysisType = this.value;
            const tokenInputDiv = document.querySelector('.token-input');
            const addressInputDiv = document.querySelector('.address-input');
            const tokenInput = tokenInputDiv ? tokenInputDiv.querySelector('input') : null;
            const addressInput = addressInputDiv ? addressInputDiv.querySelector('input') : null;

            if (!tokenInputDiv || !addressInputDiv || !tokenInput || !addressInput) return; // Exit if elements not found

            if (analysisType === 'ico' || analysisType === 'rugpull') {
                tokenInputDiv.style.display = 'block';
                tokenInput.required = true;
                addressInputDiv.style.display = 'none';
                addressInput.required = false;
                addressInput.value = ''; // Clear address input
            } else if (analysisType === 'all') {
                 tokenInputDiv.style.display = 'block';
                 tokenInput.required = false; // Neither is strictly required for 'all', logic handled server-side
                 addressInputDiv.style.display = 'block';
                 addressInput.required = false;
            } else { // For money_laundering, mixer, dusting, wallet, transaction
                tokenInputDiv.style.display = 'none';
                tokenInput.required = false;
                tokenInput.value = ''; // Clear token input
                addressInputDiv.style.display = 'block';
                addressInput.required = true;
            }
        });

        // Trigger change on page load to set initial state
        analysisTypeSelect.dispatchEvent(new Event('change'));
    }

    // Add other frontend logic as needed
    console.log("Sentinel AI frontend initialized.");

});

// Example function (can be expanded or removed)
function showAlert(message) {
    alert(message);
}
            