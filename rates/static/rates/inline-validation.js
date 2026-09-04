(function () {
  const config = document.getElementById("rate-validation-config");
  const token = document.querySelector("[name=csrfmiddlewaretoken]");
  if (!config || !token) {
    return;
  }

  const url = JSON.parse(config.textContent).url;
  const WATCHED = ["name", "price", "min_stay_nights", "cancellation_days"];
  const DELAY = 300;
  const rows = new WeakMap();

  function fieldOf(input) {
    if (!input.name) {
      return null;
    }
    const cut = input.name.lastIndexOf("-");
    return cut === -1 ? null : input.name.slice(cut + 1);
  }

  function payload(row) {
    const data = new FormData();
    row.querySelectorAll("input, select").forEach(function (el) {
      const field = fieldOf(el);
      if (field && WATCHED.indexOf(field) !== -1) {
        data.append(field, el.value);
      }
    });
    return data;
  }

  function clear(row) {
    row.querySelectorAll("ul.errorlist[data-live]").forEach(function (list) {
      list.remove();
    });
    row.querySelectorAll("[aria-invalid]").forEach(function (widget) {
      widget.removeAttribute("aria-invalid");
      widget.removeAttribute("aria-describedby");
    });
  }

  // Le <ul> doit etre le frere immediatement precedent du widget : c'est ce que
  // base.css utilise pour poser la bordure rouge, et c'est la place des erreurs natives.
  function paint(row, errors) {
    clear(row);
    Object.keys(errors).forEach(function (field) {
      const widget = row.querySelector('[name$="-' + field + '"]');
      if (!widget) {
        return;
      }
      const list = document.createElement("ul");
      list.className = "errorlist";
      list.id = widget.id + "_error";
      list.setAttribute("data-live", "");
      errors[field].forEach(function (message) {
        const item = document.createElement("li");
        item.textContent = message;
        list.appendChild(item);
      });
      widget.parentNode.insertBefore(list, widget);
      widget.setAttribute("aria-invalid", "true");
      widget.setAttribute("aria-describedby", list.id);
    });
  }

  // inlines.js renumerote les lignes restantes apres une suppression, donc une reponse
  // en vol peut revenir sur une ligne qui a change d'index. On indexe par noeud et par
  // numero d'ordre, jamais par prefixe.
  function validate(row) {
    const slot = rows.get(row) || {};
    if (slot.controller) {
      slot.controller.abort();
    }
    slot.controller = new AbortController();
    slot.seq = (slot.seq || 0) + 1;
    rows.set(row, slot);

    const mine = slot.seq;
    fetch(url, {
      method: "POST",
      body: payload(row),
      headers: { "X-CSRFToken": token.value },
      signal: slot.controller.signal,
    })
      .then(function (response) {
        return response.ok ? response.json() : null;
      })
      .then(function (data) {
        const current = rows.get(row);
        if (!data || !current || current.seq !== mine || !row.isConnected) {
          return;
        }
        paint(row, data.errors);
      })
      .catch(function () {
        // Reseau coupe ou requete annulee : on laisse la ligne telle quelle
        // plutot que d'afficher un verdict que le serveur n'a pas rendu.
      });
  }

  function schedule(event) {
    const input = event.target;
    const field = fieldOf(input);
    if (!field || WATCHED.indexOf(field) === -1) {
      return;
    }
    const row = input.closest("tr");
    if (!row) {
      return;
    }
    const slot = rows.get(row) || {};
    clearTimeout(slot.timer);
    slot.timer = setTimeout(function () {
      validate(row);
    }, DELAY);
    rows.set(row, slot);
  }

  document.addEventListener("input", schedule);
  document.addEventListener("change", schedule);
})();
