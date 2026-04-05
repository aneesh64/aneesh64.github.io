---
title: "Posts by Category"
permalink: /categories/
---

{% assign sorted_categories = site.categories | sort %}
{% for category in sorted_categories %}
<section class="taxonomy-group">
	<h3>{{ category[0] }}</h3>
	<p class="taxonomy-count">{{ category[1].size }} post{% if category[1].size != 1 %}s{% endif %}</p>
	<ul>
		{% for post in category[1] %}
		<li><a href="{{ post.url | relative_url }}">{{ post.title }}</a> <span class="taxonomy-count">{{ post.date | date: "%Y-%m-%d" }}</span></li>
		{% endfor %}
	</ul>
</section>
{% endfor %}
