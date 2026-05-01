---
layout: archive
title: "Publications"
description: "Selected peer-reviewed publications by Gang Zhao on flood modelling, flash flood warning, hydrology, hydrodynamics, and flood risk."
permalink: /publications/
author_profile: true
---

{% if site.author.googlescholar %}
  <div class="wordwrap">You can find my all articles on
    <a href="{{ site.author.googlescholar }}">my Google Scholar profile</a>.
  </div>
{% endif %}

{% include base_path %}

<style>
  /* 简洁一点的行距 */
  ol.publist { padding-left: 1.25em; }
  ol.publist li { margin: 0.35em 0; }
</style>

{%- comment -%} ===== Peer-reviewed（近五年） ===== {%- endcomment -%}
{% assign cutoff_year = site.time | date: "%Y" | plus: 0 | minus: 5 %}
{% assign published = site.publications | reject: "status", "under review" | sort: "date" | reverse %}

## Peer-reviewed (last five years)
{% assign pubs = site.data.pubs_orcid %}
<ol class="publist">
  {% for p in pubs %}
    <li>
      {{ p.authors | default: site.author.name }}{% if p.publication_date %} ({{ p.publication_date | date: "%Y" }}){% endif %}.
      {{ p.title }}.
      {% if p.venue %}<em>{{ p.venue }}</em>.{% endif %}
      {% if p.doi %}<a href="https://doi.org/{{ p.doi }}">doi:{{ p.doi }}</a>{% endif %}
    </li>
  {% endfor %}
</ol>
