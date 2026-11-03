/* Enhance documentation images without changing their Markdown or original files. */
(() => {
  "use strict";

  function initialise() {
    const content = document.querySelector(".rst-content");
    if (!content || content.dataset.imageViewerReady) return;
    content.dataset.imageViewerReady = "true";

    const images = Array.from(content.querySelectorAll("img"))
      .filter(image => !image.closest("[data-no-image-viewer]"));
    if (!images.length) return;

    const entries = images.map(image => {
      const source = image.dataset.fullSize || image.currentSrc || image.src;
      let figure = image.closest("figure");
      if (!figure) {
        figure = document.createElement("figure");
        const wrapper = image.closest("a") || image;
        const paragraph = wrapper.parentElement;
        if (paragraph.tagName === "P" && paragraph.children.length === 1 && !paragraph.textContent.trim()) {
          paragraph.replaceWith(figure);
        } else {
          wrapper.before(figure);
        }
        figure.append(wrapper);
        if (image.alt) {
          const caption = document.createElement("figcaption");
          caption.textContent = image.alt;
          figure.append(caption);
        }
      }
      figure.classList.add("doc-image-figure");
      const paragraph = image.closest("p");
      if (paragraph && paragraph.children.length === 1) paragraph.classList.add("doc-image-paragraph");
      const caption = figure.querySelector("figcaption");
      const title = (caption ? caption.textContent.trim() : image.alt) || "Image";
      let link = image.closest("a");
      if (!link) {
        link = document.createElement("a");
        link.href = source;
        image.replaceWith(link);
        link.append(image);
      }
      link.classList.add("doc-image-link");
      link.setAttribute("aria-label", `Enlarge ${title}`);
      const hint = document.createElement("span");
      hint.className = "doc-image-enlarge";
      hint.textContent = "Enlarge";
      hint.setAttribute("aria-hidden", "true");
      link.append(hint);
      return {source, title, alt: image.alt || title, link};
    });

    // Older browsers still get readable previews and ordinary image links.
    if (typeof HTMLDialogElement === "undefined") return;

    const dialog = document.createElement("dialog");
    dialog.className = "doc-image-viewer";
    dialog.setAttribute("aria-labelledby", "doc-image-viewer-title");
    dialog.innerHTML = `
      <div class="doc-image-viewer__header">
        <div class="doc-image-viewer__heading">
          <h2 class="doc-image-viewer__title" id="doc-image-viewer-title"></h2>
          <p class="doc-image-viewer__meta"></p>
        </div>
        <button type="button" class="doc-image-viewer__button" data-action="close" aria-label="Close image viewer">Close</button>
      </div>
      <div class="doc-image-viewer__toolbar">
        <div class="doc-image-viewer__tools">
          <button type="button" class="doc-image-viewer__button" data-action="previous" aria-label="Previous image">←</button>
          <span class="doc-image-viewer__counter" aria-live="polite"></span>
          <button type="button" class="doc-image-viewer__button" data-action="next" aria-label="Next image">→</button>
        </div>
        <div class="doc-image-viewer__tools">
          <button type="button" class="doc-image-viewer__button" data-action="fit" aria-pressed="true">Fit</button>
          <button type="button" class="doc-image-viewer__button" data-action="actual" aria-pressed="false">100%</button>
          <button type="button" class="doc-image-viewer__button" data-action="minus" aria-label="Zoom out">−</button>
          <output class="doc-image-viewer__percent" aria-label="Zoom level" aria-live="polite"></output>
          <button type="button" class="doc-image-viewer__button" data-action="plus" aria-label="Zoom in">+</button>
        </div>
      </div>
      <div class="doc-image-viewer__stage" aria-label="Enlarged image; drag to pan when zoomed">
        <div class="doc-image-viewer__pan"><img class="doc-image-viewer__image" alt="" draggable="false" hidden></div>
        <p class="doc-image-viewer__status" role="status">Loading image…</p>
      </div>
      <div class="doc-image-viewer__footer">
        <span class="doc-image-viewer__help">Esc to close · Arrow keys to browse</span>
        <a class="doc-image-viewer__original" target="_blank" rel="noopener">Open original</a>
      </div>`;
    document.body.append(dialog);

    const select = selector => dialog.querySelector(selector);
    const action = name => select(`[data-action="${name}"]`);
    const stage = select(".doc-image-viewer__stage");
    const pan = select(".doc-image-viewer__pan");
    const full = select(".doc-image-viewer__image");
    const status = select(".doc-image-viewer__status");
    const fitButton = action("fit");
    const actualButton = action("actual");
    const zoomOut = action("minus");
    const zoomIn = action("plus");
    let index = 0, zoom = 1, fitZoom = 1, mode = "fit", ready = false, opener = null, drag = null;

    function update() {
      if (!ready) return;
      const width = Math.round(full.naturalWidth * zoom);
      const height = Math.round(full.naturalHeight * zoom);
      full.style.width = `${width}px`;
      full.style.height = `${height}px`;
      pan.style.width = `${Math.max(stage.clientWidth, width + 32)}px`;
      pan.style.height = `${Math.max(stage.clientHeight, height + 32)}px`;
      select(".doc-image-viewer__percent").textContent = `${Math.round(zoom * 100)}%`;
      fitButton.setAttribute("aria-pressed", String(mode === "fit"));
      actualButton.setAttribute("aria-pressed", String(mode === "actual"));
      const canPan = zoom > fitZoom + 0.001;
      stage.classList.toggle("is-zoomed", canPan);
      select(".doc-image-viewer__help").textContent = canPan
        ? "Drag to pan · Esc to close" : "Esc to close · Arrow keys to browse";
      zoomOut.disabled = zoom <= Math.min(fitZoom, 0.1) + 0.001;
      zoomIn.disabled = zoom >= 4;
    }

    function fit() {
      if (!ready || !dialog.open) return;
      fitZoom = Math.min((stage.clientWidth - 32) / full.naturalWidth, (stage.clientHeight - 32) / full.naturalHeight, 1);
      zoom = fitZoom;
      mode = "fit";
      update();
      stage.scrollLeft = stage.scrollTop = 0;
    }

    function setZoom(value, nextMode = "zoom") {
      if (!ready) return;
      const centerX = (stage.scrollLeft + stage.clientWidth / 2 - (pan.clientWidth - full.width) / 2) / zoom;
      const centerY = (stage.scrollTop + stage.clientHeight / 2 - (pan.clientHeight - full.height) / 2) / zoom;
      zoom = Math.max(Math.min(fitZoom, 0.1), Math.min(4, value));
      mode = nextMode;
      update();
      stage.scrollLeft = centerX * zoom + (pan.clientWidth - full.width) / 2 - stage.clientWidth / 2;
      stage.scrollTop = centerY * zoom + (pan.clientHeight - full.height) / 2 - stage.clientHeight / 2;
    }

    function show(next) {
      index = (next + entries.length) % entries.length;
      const entry = entries[index];
      ready = false;
      drag = null;
      stage.classList.remove("is-zoomed", "is-dragging");
      full.hidden = true;
      status.textContent = "Loading image…";
      status.hidden = false;
      select(".doc-image-viewer__title").textContent = entry.title;
      select(".doc-image-viewer__meta").textContent = "";
      select(".doc-image-viewer__counter").textContent = `${index + 1} / ${entries.length}`;
      select(".doc-image-viewer__percent").textContent = "";
      select(".doc-image-viewer__original").href = entry.source;
      if ([fitButton, actualButton, zoomOut, zoomIn].includes(document.activeElement)) action("close").focus();
      [fitButton, actualButton, zoomOut, zoomIn].forEach(button => { button.disabled = true; });
      full.onload = () => {
        ready = true;
        full.hidden = false;
        status.hidden = true;
        select(".doc-image-viewer__meta").textContent = `${full.naturalWidth} × ${full.naturalHeight} px`;
        [fitButton, actualButton, zoomOut, zoomIn].forEach(button => { button.disabled = false; });
        fit();
      };
      full.onerror = () => { status.textContent = "This image could not be loaded. Try Open original."; };
      full.alt = entry.alt;
      full.src = entry.source;
    }

    entries.forEach((entry, position) => {
      entry.link.setAttribute("aria-haspopup", "dialog");
      entry.link.addEventListener("click", event => {
        if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        opener = entry.link;
        dialog.showModal();
        document.body.classList.add("doc-image-viewer-open");
        show(position);
        action("close").focus();
      });
    });
    action("close").addEventListener("click", () => dialog.close());
    action("previous").addEventListener("click", () => show(index - 1));
    action("next").addEventListener("click", () => show(index + 1));
    fitButton.addEventListener("click", fit);
    actualButton.addEventListener("click", () => setZoom(1, "actual"));
    zoomIn.addEventListener("click", () => setZoom(zoom * 1.4));
    zoomOut.addEventListener("click", () => setZoom(zoom / 1.4));
    dialog.addEventListener("close", () => {
      document.body.classList.remove("doc-image-viewer-open");
      drag = null;
      if (opener) opener.focus({preventScroll: true});
    });
    dialog.addEventListener("click", event => {
      if (event.target !== dialog) return;
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
    });
    dialog.addEventListener("keydown", event => {
      const actions = {
        ArrowRight: () => show(index + 1), ArrowLeft: () => show(index - 1),
        "+": () => setZoom(zoom * 1.4), "=": () => setZoom(zoom * 1.4), "-": () => setZoom(zoom / 1.4),
      };
      if (actions[event.key]) { event.preventDefault(); actions[event.key](); }
    });
    stage.addEventListener("pointerdown", event => {
      if (event.button !== 0 || !stage.classList.contains("is-zoomed")) return;
      drag = {x: event.clientX, y: event.clientY, left: stage.scrollLeft, top: stage.scrollTop};
      stage.setPointerCapture(event.pointerId);
      stage.classList.add("is-dragging");
    });
    stage.addEventListener("pointermove", event => {
      if (!drag) return;
      stage.scrollLeft = drag.left + drag.x - event.clientX;
      stage.scrollTop = drag.top + drag.y - event.clientY;
    });
    const stopDrag = () => { drag = null; stage.classList.remove("is-dragging"); };
    stage.addEventListener("pointerup", stopDrag);
    stage.addEventListener("pointercancel", stopDrag);
    window.addEventListener("resize", () => { if (mode === "fit") fit(); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialise);
  else initialise();
})();
