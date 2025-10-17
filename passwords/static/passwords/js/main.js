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
function selectService(serviceName) {
    const input = document.querySelector('input[name="input"]');
    const suggestionsEl = document.getElementById("suggestions");

    input.value = serviceName;

    // Hide suggestions
    suggestionsEl.innerHTML = '';
    suggestionsEl.style.display = 'none';

    sendRequest(serviceName);
}

// Main search function - simplified and modernized
function handleSearch() {
    const input = document.querySelector('input[name="input"]').value.trim();
    const suggestionsEl = document.getElementById("suggestions");
    const outputEl = document.getElementById("output");

    // Clear previous results
    suggestionsEl.innerHTML = '';
    suggestionsEl.style.display = 'none';
    outputEl.innerHTML = '';

    if (!input) return;

    // Find exact match first
    const exactMatch = list.find(service =>
        normalizeString(service) === normalizeString(input)
    );

    if (exactMatch) {
        sendRequest(exactMatch);
        return;
    }

    // Show suggestions for partial matches
    const suggestions = list
        .filter(service =>
            normalizeString(service).startsWith(normalizeString(input))
        )
        .sort((a, b) => a.localeCompare(b))
        .slice(0, 6); // Limit to 6 suggestions

    if (suggestions.length > 0) {
        suggestions.forEach(service => {
            const suggestionEl = document.createElement("span");
            suggestionEl.id = "suggestion";
            suggestionEl.textContent = service;
            suggestionEl.addEventListener('click', () => selectService(service));
            suggestionsEl.appendChild(suggestionEl);
        });
        suggestionsEl.style.display = 'inline-block';
    }
}

async function sendRequest(data) {
    const outputElement = document.getElementById("output");

    // Show loading message
    fillElement(outputElement, "Retrieving data...");

    try {
        const response = await fetch(fetchDataUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCookie('csrftoken')
            },
            body: "item=" + data
        });

        const jsonData = await response.json();

        if (response.ok) {
            // Generate HTML from JSON data
            const html = generateEntryHTML(jsonData);
            fillElement(outputElement, html);
        } else {
            // Handle error response
            fillElement(outputElement, `<div class="error">Error: ${jsonData.error}</div>`);
        }
    } catch (error) {
        fillElement(outputElement, '<div class="error">Error retrieving data</div>');
    }
}

// Generate HTML elements from JSON password data
function generateEntryHTML(data) {
    let html = `<div class="entry-field">
        <div class="field-label">Service:</div>
        <div class="field-value"><strong>${escapeHtml(data.service_name)}</strong></div>`;

    if (data.service_url) {
        html += `<div class="field-label">URL:</div>
        <div class="field-value"><a href="${escapeHtml(data.service_url)}" target="_blank">${escapeHtml(data.service_url)}</a></div>`;
    }

    html += `<div class="field-label">Username:</div>
        <div class="field-value">${escapeHtml(data.username)}</div>
        <div class="field-label">Password:</div>
        <div class="field-value">${escapeHtml(data.password)}</div>`;

    if (data.comments) {
        html += `<div class="field-label">Notes:</div>
        <div class="field-value">${escapeHtml(data.comments)}</div>`;
    }

    html += `</div>`;

    return html;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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