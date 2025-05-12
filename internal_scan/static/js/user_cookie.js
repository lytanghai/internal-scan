let configData = {};

function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
}

function modify_arr_cookie(name, value, action) {
    let c_workspaces = getCookie(name);
    try {
        c_workspaces = JSON.parse(c_workspaces || '[]');

    } catch (e) {
        c_workspaces = [];
    }

    if (action === 'append') {
        if (!c_workspaces.includes(value)) {
            c_workspaces.push(value);
        }
    } else if (action === 'remove') {
        const index = c_workspaces.indexOf(value);
        if (index !== -1) {
            c_workspaces.splice(index, 1);
        }
    }

    document.cookie = `${name}=${JSON.stringify(c_workspaces)}; path=/; max-age=604800`; // 7 days
}


document.getElementById("user_config_file").addEventListener("change", function (event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = function (e) {
        try {
            const configData = JSON.parse(e.target.result);

            for (const [key, value] of Object.entries(configData)) {
                setCookie(key, JSON.stringify(value), 7);
            }

            alert("Config uploaded and stored in cookies for 7 days.");
        } catch (err) {
            console.error("Invalid JSON:", err);
            alert("Failed to read config file. Make sure it's valid JSON.");
        }
    };

    reader.readAsText(file);
});

function getCookie(name) {
    return document.cookie.split('; ').reduce((r, v) => {
        const parts = v.split('=');
        return parts[0] === name ? decodeURIComponent(parts[1]) : r;
    }, '');
}

function getCookieWithDefault(name, defaultValue) {
  const value = getCookie(name);
  return value && !isNaN(value) ? parseInt(value) : defaultValue;
}

const configJson = getCookie("config_data");
const config = configJson ? JSON.parse(configJson) : null;