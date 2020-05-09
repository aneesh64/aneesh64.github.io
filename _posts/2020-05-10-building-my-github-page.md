---
title: "Building my github page"
date: 2020-05-09T10:34:30-04:00
categories:
  - Blog
tags:
  - update
  - website
  - github pages
classes: wide
---

This is 2020. We are currently in the middle of a pandemic that is ravaging the earth. (Well, sounds dramatic, and is intended to be that way by the author of this blog post as well (why am I addressing myself in third person? Apparently there is a term for this: [illeism][illeism]). I should probably spend less time on twitter at least. Ignorance is truly a bliss as they say.) In these trying times, I set out to make my own website. As you can see in the [About][about_me] section, I studied electrical and computer engineering in college. I have written softwares in common languages like C/C++, Python and Verilog/VHDL used for programming the FPGAs. This is the first time, I am setting my foot on the web side of things. Anyway, at first I considered writing on [medium][medium] and this would have been probably the easiest way to directly start blogging and reach people (that is, my family and friends, that too if they have nothing holding them up). For a considerable time now, I have been reading medium posts from awesome people on any topic under the sun.

However, I wanted something more customizable and flexible. I set on a [googling][googling] journey to find out the best way to get a blog post up and running fast. (I do this ritual of finding information on web on almost everything, the ritual that is practiced by people all over the world. [Why is this a ritual? Good question.]) Since I already knew quite a bit of Python, I set out to find the best framework for building simple static websites and boom! [Flask][flask_page] seemed the obvious choice. Opened up a tutorial, starting from basic HTML layouts and the philosophy behind Flask design. I realized quickly, that building the page from scratch is going to take a long time, and I was not sure if I wanted to invest my time on learning the intricacies of HTML and website design. 

I still wanted a personal website, but without building everything from bottom up. At this point of time, I felt the github pages is a better bet, as the hosting of the page was free of cost, and I did see a lot of github personal pages of people in tech. Also, it was easier to setup and to get the personal github page up and running took a lot less time, lesser than finishing 2 chapters of the initial Flask tutorial. Github pages uses [Jekyll][jekyll-home], a static site generator and is written in Ruby (as far as I can tell). I can write my blog posts in Markdown language in my favorite text editor (as of now its sublime) and the posts get updated on the blog. I am still learning about the Markdown langauge, but the simplicity of it is very exciting. The theme used for this page design is [minimal mistakes][minimal_mistakes], this seemed enough for my needs, and can be easily extended when I need some flashy and complicated stuff on my page.

I will try to maintain some links for tutorials or pages which are useful for the website build and generation, so that anyone (most probably its going to be only me) can use these later for improvements of their personal pages.

Simple tutorial for markdown : [Markdown Tutorial] [mk_tutorial]

Github page supported emojis: [Emojis] [emojis]

This is a good tutorial on modifying the theme: [link](https://www.cross-validated.com/Personal-website-with-Minimal-Mistakes-Jekyll-Theme-HOWTO-Part-II/)

[illeism]: https://www.quickanddirtytips.com/education/grammar/whats-it-called-when-you-refer-to-yourself-by-name
[medium]: https://www.medium.com
[googling]: https://english.stackexchange.com/questions/144797/does-the-word-googling-exist
[flask_page]: https://flask.palletsprojects.com/en/1.1.x/
[about_me]: /about
[jekyll-home]: https://jekyllrb.com/
[minimal_mistakes]:https://mmistakes.github.io/minimal-mistakes/
[mk_tutorial]: https://agea.github.io/tutorial.md/
[emojis]: https://gist.github.com/rxaviers/7360908