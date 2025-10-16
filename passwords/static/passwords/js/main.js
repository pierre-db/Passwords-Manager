// Password manager JavaScript - converted from original main.js

// Empties an element
function emptyElement(elt) {
    while(elt.lastChild)
        elt.removeChild(elt.lastChild);
}

// Fills an element with HTML content
function fillElement(elt, str) {
    elt.innerHTML = str;
}

// Selects all text in input (modern browsers)
function selectChars(input) {
    input.focus();
    input.select();
}

// Modern normalize function for accented characters
function normalizeString(str) {
    return str
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, ''); // Remove diacritics
}

// Select a service from suggestions
function selectService(index) {
    const input = document.querySelector('input[name="input"]');
    input.value = list[index];
    handleSearch(index);
}

// Main search function - simplified and modernized
function handleSearch(serviceIndex = -1) {
    const input = document.querySelector('input[name="input"]').value.trim();
    const suggestionsEl = document.getElementById("suggestions");
    const outputEl = document.getElementById("output");

    // Clear previous results
    suggestionsEl.innerHTML = '';
    suggestionsEl.style.display = 'none';
    outputEl.innerHTML = '';

    if (!input) return;

    // If specific service index provided, fetch that service
    if (serviceIndex >= 0) {
        sendRequest(serviceIndex);
        return;
    }

    // Find exact match first
    const exactMatch = list.findIndex(service =>
        normalizeString(service) === normalizeString(input)
    );

    if (exactMatch >= 0) {
        sendRequest(exactMatch);
        return;
    }

    // Show suggestions for partial matches
    const suggestions = list
        .map((service, index) => ({ service, index }))
        .filter(({ service }) =>
            normalizeString(service).startsWith(normalizeString(input))
        )
        .sort((a, b) => a.service.localeCompare(b.service))
        .slice(0, 6); // Limit to 6 suggestions

    if (suggestions.length > 0) {
        suggestions.forEach(({ service, index }) => {
            const suggestionEl = document.createElement("span");
            suggestionEl.id = "suggestion";
            suggestionEl.textContent = service;
            suggestionEl.addEventListener('click', () => selectService(index));
            suggestionsEl.appendChild(suggestionEl);
        });
        suggestionsEl.style.display = 'inline-block';
    }
}

async function sendRequest(data) {
    const outputElement = document.getElementById("output");

    // Show loading message
    fillElement(outputElement, "Recupération des données...");

    try {
        const response = await fetch(fetchDataUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCookie('csrftoken')
            },
            body: "item=" + data
        });

        if (response.ok) {
            const output = await response.text();
            fillElement(outputElement, output.trim());
        } else {
            fillElement(outputElement, "Erreur lors de la récupération des données");
        }
    } catch (error) {
        fillElement(outputElement, "Erreur lors de la récupération des données");
    }
}

// Get CSRF token for Django
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}