/* External sites may reject iframe navigation from the Google Sites embed. */
(function () {
  "use strict";

  document.querySelectorAll("a[href]").forEach(function (link) {
    var destination;
    try {
      destination = new URL(link.href, document.baseURI);
    } catch (error) {
      return;
    }

    // Keep site navigation, section anchors and email links in their usual context.
    if (!/^https?:$/.test(destination.protocol) || destination.origin === window.location.origin) {
      return;
    }

    link.setAttribute("target", "_blank");
    link.relList.add("noopener", "noreferrer");
    if (!link.hasAttribute("title")) {
      link.setAttribute("title", "Opens in a new tab");
    }
  });
}());
