---
title: "Posts by Year"
permalink: /posts/
---

{% assign posts_by_year = site.posts | group_by_exp: "post", "post.date | date: '%Y'" %}
{% for year in posts_by_year %}
<section class="year-group">
	<h3>{{ year.name }}</h3>
	<ul>
		{% for post in year.items %}
		<li><a href="{{ post.url | relative_url }}">{{ post.title }}</a> <span class="taxonomy-count">{{ post.date | date: "%b %d" }}</span></li>
		{% endfor %}
	</ul>
</section>
{% endfor %}
