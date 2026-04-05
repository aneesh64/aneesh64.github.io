---
title: "Posts by Tag"
permalink: /tags/
---

{% assign sorted_tags = site.tags | sort %}
{% for tag in sorted_tags %}
<section class="taxonomy-group">
	<h3>#{{ tag[0] }}</h3>
	<p class="taxonomy-count">{{ tag[1].size }} post{% if tag[1].size != 1 %}s{% endif %}</p>
	<ul>
		{% for post in tag[1] %}
		<li><a href="{{ post.url | relative_url }}">{{ post.title }}</a> <span class="taxonomy-count">{{ post.date | date: "%Y-%m-%d" }}</span></li>
		{% endfor %}
	</ul>
</section>
{% endfor %}
