---
layout: archive
title: "Publications"
permalink: /publications/
author_profile: true
---

{% if site.author.googlescholar %}
  <div class="wordwrap">You can also find my articles on <a href="{{site.author.googlescholar}}">my Google Scholar profile</a>.</div>
{% endif %}

{% include base_path %}

## Under review
{% assign under_review = site.publications | where: "status", "under review" %}
{% for post in under_review %}
  {% include archive-single.html %}
{% endfor %}

## Peer-reviewed (last five years)
{% assign peer = site.publications | reject: "status", "under review" %}
{% for post in peer reversed %}
  {% include archive-single.html %}
{% endfor %}
