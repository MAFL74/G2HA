/* G2HA Device Browser - first frontend draft. */
class G2haDeviceBrowser extends HTMLElement {
  constructor() {
    super();
    this._rendered = false;
    this._inventorySignature = "";
    this._knownEntityIds = new Set();
  }

  getCardSize() {
    return 8;
  }

  setConfig(config) {
    if (this._rendered && this.config) return;
    this.config = {
      entity: "sensor.g2ha_relay_synced_devices",
      ...config,
    };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    if (!this._expanded) this._expanded = new Set();
    if (this._query === undefined) this._query = "";
    if (this._type === undefined) this._type = "all";
    if (this._room === undefined) this._room = "all";
    if (!this._selected) this._selected = new Set();
    this._render();
  }

  set hass(value) {
    this._hass = value;
    const signature = this._inventorySignatureForRender();
    if (this.config && signature !== this._inventorySignature && !this._interacting) {
      this._inventorySignature = signature;
      this._render();
      this._rendered = true;
    }
  }

  _inventorySignatureForRender() {
    const state = this._hass?.states?.[this.config?.entity];
    const inventory = state?.attributes?.inventory;
    const syncedDevices = state?.attributes?.synced_devices;
    const rawDevices = inventory || syncedDevices || [];
    const devices = Array.isArray(rawDevices) ? rawDevices : [];
    return JSON.stringify(devices.map((device) => [
      device?.id || device?.entity_id,
      device?.name,
      device?.type,
      device?.room,
      device?.exposed,
      device?.available,
    ]));
  }

  _devices() {
    const state = this._hass?.states?.[this.config.entity];
    const inventory = state?.attributes?.inventory;
    const syncedDevices = state?.attributes?.synced_devices;
    const rawDevices = inventory || syncedDevices || [];
    const devices = (Array.isArray(rawDevices) ? rawDevices : (rawDevices && typeof rawDevices === "object" ? Object.values(rawDevices) : []))
      .filter((device) => device && typeof device === "object")
      .map((device) => ({ ...device, entity_id: device.entity_id || device.id }))
      .filter((device) => device.entity_id);
    devices.forEach((device) => {
      if (!this._knownEntityIds.has(device.entity_id)) {
        if (device.exposed) this._selected.add(device.entity_id);
        this._knownEntityIds.add(device.entity_id);
      }
    });
    return devices;
  }

  _friendlyType(type) {
    const names = {
      LIGHT: "Lights", OUTLET: "Switches", SWITCH: "Switches", FAN: "Fans",
      THERMOSTAT: "Climate", WATERHEATER: "Climate", HUMIDIFIER: "Climate",
      DEHUMIDIFIER: "Climate", AIRPURIFIER: "Climate", VACUUM: "Vacuums",
      LOCK: "Locks", TV: "Media players", CAMERA: "Cameras", BLINDS: "Covers",
      SENSOR: "Sensors", BINARY_SENSOR: "Sensors",
    };
    return names[type?.split(".").pop()] || "Other";
  }

  _icon(type) {
    const icons = {
      Lights: "💡", Switches: "🔌", Fans: "🌀", Climate: "🌡️", Vacuums: "🤖",
      Locks: "🔒", "Media players": "📺", Cameras: "📷", Covers: "🪟",
      Sensors: "📊", Other: "•",
    };
    return icons[type] || "•";
  }

  _roomName(device) {
    return String(device.room || "").trim() || "No room assigned";
  }

  _escape(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[character]);
  }

  _status(device) {
    const state = device.state || {};
    const values = Object.values(state).flatMap((value) =>
      value && typeof value === "object" ? Object.values(value) : [value],
    );
    if (device.available === false || values.some((value) => ["unavailable", "unknown"].includes(String(value).toLowerCase()))) {
      return "Unavailable";
    }
    if (state.on !== undefined) return state.on ? "On" : "Off";
    if (state.openPercent !== undefined) return `${state.openPercent}%`;
    if (state.currentStatus !== undefined) return String(state.currentStatus);
    if (state.currentModeSettings !== undefined) return String(state.currentModeSettings);
    return "Available";
  }

  _applySearch() {
    const query = this._query.toLowerCase().trim();
    this.shadowRoot.querySelectorAll("details[data-group]").forEach((group) => {
      let visible = 0;
      group.querySelectorAll(".device").forEach((device) => {
        const matches = !query || (device.dataset.search || "").includes(query);
        device.hidden = !matches;
        if (matches) visible += 1;
      });
      group.hidden = visible === 0;
      const count = group.querySelector(".group-count");
      if (count) count.textContent = `${visible} devices`;
    });
    const visible = [...this.shadowRoot.querySelectorAll(".device")].filter((device) => !device.hidden).length;
    const summary = this.shadowRoot.querySelector(".summary");
    const devices = this._devices();
    const exposed = devices.filter((device) => this._selected.has(device.entity_id)).length;
    if (summary) summary.textContent = `${visible} of ${devices.length} available entities · ${exposed} synchronized with Google Home`;
  }

  _render() {
    if (!this.shadowRoot || !this._hass) return;
    const active = this.shadowRoot.activeElement;
    if (active && (active.matches?.("input, select") || active.closest?.("input, select"))) return;
    const keepSearchFocus = active?.classList?.contains("search");
    const selectionStart = keepSearchFocus ? active.selectionStart : null;
    const selectionEnd = keepSearchFocus ? active.selectionEnd : null;
    const all = this._devices();
    const query = this._query.toLowerCase();
    const filtered = all.filter((device) => {
      const type = this._friendlyType(device.type);
        const room = this._roomName(device);
      return (this._type === "all" || type === this._type)
        && (this._room === "all" || room === this._room);
    });
    const groups = [...new Set(filtered.map((device) => this._friendlyType(device.type)))].sort();
    const total = all.length;
    const selectedCount = all.reduce((count, device) => count + (this._selected.has(device.entity_id) ? 1 : 0), 0);
    const types = [...new Set(all.map((device) => this._friendlyType(device.type)))].sort();
    const rooms = [...new Set(all.map((device) => this._roomName(device)))].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
    const escape = (value) => this._escape(value);
    this.shadowRoot.innerHTML = `<style>
      :host { display:block; }
      ha-card { padding: 18px; }
      .toolbar { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:16px; }
      input, select { background:var(--card-background-color); color:var(--primary-text-color); border:1px solid var(--divider-color); border-radius:10px; padding:11px 12px; font:inherit; }
      input { flex:1 1 240px; }
      select { flex:1 1 170px; min-width:170px; }
      .summary { color:var(--secondary-text-color); margin:0 0 14px; font-size:.9em; }
      details { border:1px solid var(--divider-color); border-radius:12px; margin:10px 0; overflow:hidden; background:var(--card-background-color); }
      summary { cursor:pointer; list-style:none; padding:14px 16px; font-weight:600; background:var(--secondary-background-color); transition:background .15s ease; }
      summary:hover { background:var(--primary-background-color); }
      summary::-webkit-details-marker { display:none; }
      .group-count { float:right; color:var(--secondary-text-color); font-weight:500; font-size:.9em; }
      .device { display:grid; grid-template-columns:28px 32px minmax(0,1fr) auto; align-items:start; gap:12px; padding:13px 16px; border-top:1px solid var(--divider-color); cursor:pointer; transition:background .15s ease; }
      .device:hover { background:var(--secondary-background-color); }
      .device-icon { font-size:21px; width:32px; text-align:center; padding-top:2px; }
      .device-main { min-width:0; flex:1; }
      .name { font-weight:600; line-height:1.3; overflow-wrap:anywhere; }
      .room { color:var(--secondary-text-color); font-size:.84em; line-height:1.3; margin-top:3px; overflow-wrap:anywhere; }
      .traits { color:var(--secondary-text-color); font-size:.77em; line-height:1.35; margin-top:6px; white-space:normal; overflow-wrap:anywhere; word-break:break-word; }
      .status { font-weight:600; white-space:nowrap; border-radius:999px; padding:5px 9px; background:var(--secondary-background-color); font-size:.86em; }
      @media (max-width:600px) { .device { grid-template-columns:28px minmax(0,1fr); } .status { grid-column:2; justify-self:start; margin-top:6px; } }
      .empty { color:var(--secondary-text-color); padding:20px 0; }
      .selection { color:var(--primary-color); transform:scale(1.2); margin-top:5px; }
      .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin:0 0 14px; }
      button { background:var(--primary-color); color:var(--text-primary-color); border:0; border-radius:10px; padding:10px 14px; font:inherit; cursor:pointer; }
      .selected { color:var(--secondary-text-color); font-size:.9em; }
    </style>
    <ha-card>
      <div class="toolbar"><input class="search" aria-label="Search devices" placeholder="Search devices" value="${escape(this._query)}"><select class="type" aria-label="Filter by type"><option value="all">All types</option>${types.map(t => `<option value="${escape(t)}" ${t === this._type ? "selected" : ""}>${escape(t)}</option>`).join("")}</select><select class="room" aria-label="Filter by room"><option value="all">All rooms</option>${rooms.map(room => `<option value="${escape(room)}" ${room === this._room ? "selected" : ""}>${escape(room)}</option>`).join("")}</select></div>
      <div class="summary">Showing ${filtered.length} of ${total} available entities · ${selectedCount} synchronized with Google Home</div>
      <div class="actions"><button class="save">Save exposure</button><button class="save-sync">Save and sync now</button><span class="selected">Selected devices will be exposed to Google Home.</span></div>
      ${groups.length ? groups.map(group => { const items = all.filter(d => this._friendlyType(d.type) === group); const visibleItems = filtered.filter(d => this._friendlyType(d.type) === group); const open = this._expanded.has(group) ? " open" : ""; const allSelected = items.length > 0 && items.every(d => this._selected.has(d.entity_id)); const someSelected = items.some(d => this._selected.has(d.entity_id)); return `<details data-group="${escape(group)}"${open}><summary><input class="group-select" type="checkbox" data-group-select="${escape(group)}" ${allSelected ? "checked" : ""} ${someSelected && !allSelected ? "data-indeterminate=true" : ""}> ${this._icon(group)} ${escape(group)}<span class="group-count">${items.length} devices</span></summary>${visibleItems.map(d => { const room = this._roomName(d); const searchText = [d.name, d.entity_id, room].join(" ").toLowerCase(); const traits = Array.isArray(d.traits) ? d.traits.join(", ") : String(d.traits || ""); return `<div class="device" data-entity="${escape(d.entity_id)}" data-search="${escape(searchText)}"><input class="selection" type="checkbox" data-select="${escape(d.entity_id)}" ${this._selected.has(d.entity_id) ? "checked" : ""}><div class="device-icon">${this._icon(group)}</div><div class="device-main"><div class="name">${escape(d.name)}</div><div class="room">${escape(room)}</div><div class="traits">${escape(traits)}</div></div><div class="status">${escape(this._status(d))}</div></div>`; }).join("")}</details>`; }).join("") : '<div class="empty">No devices found.</div>'}
    </ha-card>`;
    this.shadowRoot.querySelector(".search")?.addEventListener("input", (event) => { this._query = event.target.value; this._applySearch(); });
    this.shadowRoot.querySelector(".type")?.addEventListener("change", (event) => { this._type = event.target.value; this._render(); });
    this.shadowRoot.querySelector(".room")?.addEventListener("change", (event) => { this._room = event.target.value; this._render(); });
    const save = async (sync) => { await this._hass.callService("g2ha", "set_exposure", { entity_ids: [...this._selected] }); if (sync) await this._hass.callService("button", "press", { entity_id: "button.g2ha_relay_force_sync_now" }); };
    this.shadowRoot.querySelector(".save")?.addEventListener("click", () => save(false));
    this.shadowRoot.querySelector(".save-sync")?.addEventListener("click", () => save(true));
    this.shadowRoot.querySelectorAll("[data-select]").forEach((box) => box.addEventListener("click", (event) => {
      event.stopPropagation();
      if (event.target.checked) this._selected.add(event.target.dataset.select);
      else this._selected.delete(event.target.dataset.select);
      this._render();
    }));
    this.shadowRoot.querySelectorAll("[data-group-select]").forEach((box) => {
      box.indeterminate = box.dataset.indeterminate === "true";
      box.addEventListener("click", (event) => event.stopPropagation());
      box.addEventListener("change", (event) => {
        event.stopPropagation();
        const group = event.target.dataset.groupSelect;
        this._devices().filter((d) => this._friendlyType(d.type) === group).forEach((d) => {
          if (event.target.checked) this._selected.add(d.entity_id);
          else this._selected.delete(d.entity_id);
        });
        this._render();
      });
    });
    this.shadowRoot.querySelectorAll("input, select").forEach((control) => {
      control.addEventListener("focus", () => { this._interacting = true; });
      control.addEventListener("blur", () => { setTimeout(() => { this._interacting = false; }, 250); });
    });
    this.shadowRoot.querySelectorAll("details").forEach((node) => node.addEventListener("toggle", () => { if (node.open) this._expanded.add(node.dataset.group); else this._expanded.delete(node.dataset.group); }));
    this.shadowRoot.querySelectorAll(".device").forEach((node) => node.addEventListener("click", () => this.dispatchEvent(new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId: node.dataset.entity } }))));
    this._applySearch();
    if (keepSearchFocus) {
      const search = this.shadowRoot.querySelector(".search");
      search?.focus();
      if (selectionStart !== null) search?.setSelectionRange(selectionStart, selectionEnd);
    }
  }
}
if (!customElements.get("g2ha-device-browser-v5")) {
  class G2haDeviceBrowserV4 extends G2haDeviceBrowser {}
  customElements.define("g2ha-device-browser-v5", G2haDeviceBrowserV4);
}
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "custom:g2ha-device-browser-v5")) {
  window.customCards.push({
    type: "custom:g2ha-device-browser-v5",
    name: "G2HA Device Browser",
    description: "Searchable, collapsible G2HA synchronized-device browser",
    preview: true,
  });
}


