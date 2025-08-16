---
layout: archive
title: "Publications"
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

{% assign count = 0 %}

{%- comment -%} ===== Under review（若有） ===== {%- endcomment -%}
{% assign under_review = site.publications | where: "status", "under review" | sort: "date" | reverse %}
{% if under_review.size > 0 %}
## Under review
<ol class="publist" start="{{ count | plus: 1 }}">
  {% for post in under_review %}
    {% assign count = count | plus: 1 %}
    <li>
      {{ post.authors }}.
      {{ post.title }}.
      {% if post.venue %}<em>{{ post.venue }}</em>.{% endif %}
      {% if post.doi %}
        <a href="https://doi.org/{{ post.doi }}">doi:{{ post.doi }}</a>
      {% endif %}
    </li>
  {% endfor %}
</ol>
{% endif %}

{%- comment -%} ===== Peer-reviewed（近五年） ===== {%- endcomment -%}
{% assign cutoff_year = site.time | date: "%Y" | plus: 0 | minus: 5 %}
{% assign published = site.publications | reject: "status", "under review" | sort: "date" | reverse %}

## Peer-reviewed (last five years)
{% assign pubs = site.data.pubs_openalex | default: [] %}
<ol class="publist" start="{{ count | plus: 1 }}">
  {% for p in pubs %}
    {% assign count = count | plus: 1 %}
    <li>
      {{ p.authors }}.
      {{ p.title }}.
      {% if p.venue %}<em>{{ p.venue }}</em>.{% endif %}
      {% if p.doi %}<a href="https://doi.org/{{ p.doi }}">doi:{{ p.doi }}</a>{% endif %}
    </li>
  {% endfor %}
</ol>

