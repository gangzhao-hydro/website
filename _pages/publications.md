---
layout: archive
title: "Publications"
permalink: /publications/
author_profile: true
---

{% if site.author.googlescholar %}
  <div class="wordwrap">You can also find my articles on
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
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>.
      {% if post.doi %}
        <a href="https://doi.org/{{ post.doi }}">doi:{{ post.doi }}</a>
      {% elsif post.paperurl %}
        <a href="{{ post.paperurl }}">link</a>
      {% endif %}
    </li>
  {% endfor %}
</ol>
{% endif %}

{%- comment -%} ===== Peer-reviewed（近五年） ===== {%- endcomment -%}
{% assign cutoff_year = site.time | date: "%Y" | plus: 0 | minus: 5 %}
{% assign published = site.publications | reject: "status", "under review" | sort: "date" | reverse %}

## Peer-reviewed (last five years)
<ol class="publist" start="{{ count | plus: 1 }}">
  {% for post in published %}
    {% assign y = post.date | date: "%Y" | plus: 0 %}
    {% if y >= cutoff_year %}
      {% assign count = count | plus: 1 %}
      <li>
        {{ post.authors }}.
        <a href="{{ post.url | relative_url }}">{{ post.title }}</a>.
        {% if post.doi %}
          <a href="https://doi.org/{{ post.doi }}">doi:{{ post.doi }}</a>
        {% elsif post.paperurl %}
          <a href="{{ post.paperurl }}">link</a>
        {% endif %}
      </li>
    {% endif %}
  {% endfor %}
</ol>

