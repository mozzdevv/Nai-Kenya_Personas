export function formatDualTime(dateString) {
    if (!dateString) return '';
    // Ensure input is treated as UTC if no offset matches.
    // Standard SQL string 'YYYY-MM-DD HH:MM:SS' needs 'T' and 'Z' to be safely parsed as UTC.
    // If it already has T or Z, this might duplicate, so check.
    let safeDateStr = dateString;
    if (!dateString.includes('T')) {
        safeDateStr = dateString.replace(' ', 'T');
    }
    if (!safeDateStr.endsWith('Z') && !safeDateStr.includes('+')) {
        safeDateStr += 'Z';
    }

    const date = new Date(safeDateStr);

    // Format options: 24h format for clarity, or user preference. user said "HH:MM".
    // "15:00" is ambiguous in 12h without AM/PM. I'll use 24h to be safe and consistent with "HH:MM"
    // EAT is usually 24h in tech settings? Or maybe 12h.
    // User example: "[kenyan timezone time (corresponding EST time)]"
    // I'll use 12-hour format with AM/PM as it is more standard for social media dashboards.

    const eatTime = new Intl.DateTimeFormat('en-GB', {
        hour: '2-digit', minute: '2-digit', timeZone: 'Africa/Nairobi', hour12: false
    }).format(date);

    const estTime = new Intl.DateTimeFormat('en-US', {
        hour: '2-digit', minute: '2-digit', timeZone: 'America/New_York', hour12: false
    }).format(date);

    return `${eatTime} EAT (${estTime} EST)`;
}
