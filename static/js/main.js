(function () {
    const chartRoot = document.getElementById("progress-chart");
    if (chartRoot) {
        const labels = JSON.parse(chartRoot.dataset.labels || "[]");
        const scores = JSON.parse(chartRoot.dataset.scores || "[]");

        labels.forEach((label, idx) => {
            const wrap = document.createElement("div");
            wrap.className = "bar-wrap";
            wrap.innerHTML = `
                <small>${label} - ${scores[idx]}%</small>
                <div class="bar"><span style="width:${scores[idx]}%"></span></div>
            `;
            chartRoot.appendChild(wrap);
        });
    }

    const professionSelect = document.getElementById("profession-select");
    const customProfession = document.getElementById("custom-profession");
    const rolePicker = document.getElementById("role-picker");
    const rolePickerToggle = document.getElementById("role-picker-toggle");
    const rolePickerMenu = document.getElementById("role-picker-menu");
    const rolePickerLabel = document.getElementById("role-picker-label");
    const rolePickerSearch = document.getElementById("role-picker-search");
    const roleOptions = document.querySelectorAll("[data-role-option]");

    if (rolePicker && rolePickerToggle && rolePickerMenu && professionSelect) {
        const closePicker = () => {
            rolePickerMenu.classList.add("hidden");
            rolePickerToggle.setAttribute("aria-expanded", "false");
        };
        const openPicker = () => {
            rolePickerMenu.classList.remove("hidden");
            rolePickerToggle.setAttribute("aria-expanded", "true");
            if (rolePickerSearch) rolePickerSearch.focus();
        };

        rolePickerToggle.addEventListener("click", () => {
            const expanded = rolePickerToggle.getAttribute("aria-expanded") === "true";
            if (expanded) closePicker();
            else openPicker();
        });

        roleOptions.forEach((opt) => {
            opt.addEventListener("click", () => {
                const value = opt.getAttribute("data-value") || "";
                professionSelect.value = value;
                if (rolePickerLabel) rolePickerLabel.textContent = opt.textContent.trim();
                if (customProfession) customProfession.value = value;
                roleOptions.forEach((o) => o.classList.remove("active"));
                opt.classList.add("active");
                closePicker();
            });
        });

        document.addEventListener("click", (event) => {
            if (!rolePicker.contains(event.target)) closePicker();
        });

        if (rolePickerSearch) {
            rolePickerSearch.addEventListener("input", () => {
                const query = rolePickerSearch.value.trim().toLowerCase();
                roleOptions.forEach((opt) => {
                    const text = (opt.textContent || "").toLowerCase();
                    const show = !query || text.includes(query);
                    opt.style.display = show ? "block" : "none";
                });
            });
        }
    }

    const resumeInput = document.getElementById("resume-input");
    const fileTrigger = document.getElementById("file-trigger");
    const fileName = document.getElementById("file-name");
    if (resumeInput && fileTrigger && fileName) {
        fileTrigger.addEventListener("click", () => resumeInput.click());
        resumeInput.addEventListener("change", () => {
            if (resumeInput.files && resumeInput.files.length > 0) {
                fileName.textContent = resumeInput.files[0].name;
                fileTrigger.textContent = "Change Resume";
            } else {
                fileName.textContent = "No file selected";
                fileTrigger.textContent = "Choose Resume";
            }
        });
    }

    const passwordToggles = document.querySelectorAll(".password-toggle");
    passwordToggles.forEach((toggle) => {
        toggle.addEventListener("click", () => {
            const targetId = toggle.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (!input) return;
            const hidden = input.type === "password";
            input.type = hidden ? "text" : "password";
            toggle.textContent = hidden ? "Hide" : "Show";
        });
    });

    const enhancedSelects = document.querySelectorAll("select.enhance-select");
    enhancedSelects.forEach((nativeSelect) => {
        nativeSelect.classList.add("native-select-hidden");

        const wrapper = document.createElement("div");
        wrapper.className = "custom-select";

        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "custom-select-toggle";
        toggle.setAttribute("aria-expanded", "false");
        toggle.innerHTML = `<span>${nativeSelect.options[nativeSelect.selectedIndex]?.text || "Select"}</span><span class="custom-select-caret">&#9662;</span>`;

        const menu = document.createElement("div");
        menu.className = "custom-select-menu hidden";

        Array.from(nativeSelect.options).forEach((opt, idx) => {
            const optionBtn = document.createElement("button");
            optionBtn.type = "button";
            optionBtn.className = "custom-select-option";
            optionBtn.textContent = opt.text;
            if (idx === nativeSelect.selectedIndex) optionBtn.classList.add("active");
            optionBtn.addEventListener("click", () => {
                nativeSelect.selectedIndex = idx;
                nativeSelect.dispatchEvent(new Event("change", { bubbles: true }));
                toggle.querySelector("span").textContent = opt.text;
                menu.querySelectorAll(".custom-select-option").forEach((el) => el.classList.remove("active"));
                optionBtn.classList.add("active");
                menu.classList.add("hidden");
                toggle.setAttribute("aria-expanded", "false");
            });
            menu.appendChild(optionBtn);
        });

        toggle.addEventListener("click", () => {
            const expanded = toggle.getAttribute("aria-expanded") === "true";
            document.querySelectorAll(".custom-select-menu").forEach((m) => m.classList.add("hidden"));
            document.querySelectorAll(".custom-select-toggle").forEach((t) => t.setAttribute("aria-expanded", "false"));
            if (!expanded) {
                menu.classList.remove("hidden");
                toggle.setAttribute("aria-expanded", "true");
            }
        });

        document.addEventListener("click", (event) => {
            if (!wrapper.contains(event.target)) {
                menu.classList.add("hidden");
                toggle.setAttribute("aria-expanded", "false");
            }
        });

        nativeSelect.parentNode.insertBefore(wrapper, nativeSelect.nextSibling);
        wrapper.appendChild(toggle);
        wrapper.appendChild(menu);
    });

})();
