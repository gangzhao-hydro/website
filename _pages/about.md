---
permalink: /
title: "Hello and welcome to my homepage!"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

<p style="text-align: justify;">
My name is Zhao Gang (赵刚). I am currently working as an Assistant Professor at the <a href="https://www.titech.ac.jp/english/about/organization/schools/organization06">School of Environment and Society at the Tokyo Institute of Technology</a>. I research with Prof. Tsuyoshi Kinouchi. You can visit our research group website here: <a href="http://fa.depe.titech.ac.jp/kinouchi/index-j.html">木内研究室</a>.
</p>

Research interests: Flood hazard and risk
======
<p style="text-align: justify;">
Flood hazards rank among the most destructive natural disasters, causing significant economic damage and impacting millions of lives annually. A recent example is the heavy flooding at Dongting Lake in Yueyang, Hunan Province, central China. See <a href="http://english.scio.gov.cn/in-depth/2024-07/09/content_117298698.htm">this detailed report</a> for more information. This event was triggered by floodwaters from torrential rains, leading to the evacuation of over 7,000 residents after the dike burst on Friday afternoon.
The need for accurate flood hazard maps has grown significantly due to increasing severe flood events. As shown in Figure 1, statistics of major natural disasters worldwide between 1970 and 2022 indicate that floods are the predominant natural hazard, with their frequency rising substantially. Currently, flood mitigation responsibilities have shifted from being solely a governmental task to a shared responsibility among communities, insurance companies, high-tech industries, and residents in flood-prone areas. 
</p>

<p style="text-align: justify;">
<img src="../images/Figure1.jpg?raw=true" alt="Description of Figure 1">
</p>

<p style="text-align: justify;">
My research interests primarily focus on flood modeling, using physics-based models and state-of-the-art artificial intelligence (AI) techniques. I have worked with two top-tier flood research groups worldwide. My PhD research was completed at the University of Bristol under the supervision of <a href="https://www.bristol.ac.uk/people/person/Paul-Bates-9d424135-ad4d-485d-8607-648c8890b4fa/">Professor Paul Bates</a> and <a href="https://www.bristol.ac.uk/people/person/Jeffrey-Neal-f0be79ed-1273-476b-8a6f-11849893a4b4/">Professor Jeff Neal</a>, who are the developers of the LISFLOOD-FP hydrodynamic model. Afterward, I worked as a postdoctoral researcher at the global hydrodynamic group at the University of Tokyo with <a href="https://global-hydrodynamics.github.io/">Dr. Dai Yamazaki</a>, co-developing the CaMa-Flood global hydrodynamic model. Additionally, I have also collaborated with commercial companies such as FATHOM and GAIA Vision Inc. to produce commercial flood products.
</p>


Getting started
======
1. Register a GitHub account if you don't have one and confirm your e-mail (required!)
1. Fork [this repository](https://github.com/academicpages/academicpages.github.io) by clicking the "fork" button in the top right. 
1. Go to the repository's settings (rightmost item in the tabs that start with "Code", should be below "Unwatch"). Rename the repository "[your GitHub username].github.io", which will also be your website's URL.
1. Set site-wide configuration and create content & metadata (see below -- also see [this set of diffs](http://archive.is/3TPas) showing what files were changed to set up [an example site](https://getorg-testacct.github.io) for a user with the username "getorg-testacct")
1. Upload any files (like PDFs, .zip files, etc.) to the files/ directory. They will appear at https://[your GitHub username].github.io/files/example.pdf.  
1. Check status by going to the repository settings, in the "GitHub pages" section

Site-wide configuration
------
The main configuration file for the site is in the base directory in [_config.yml](https://github.com/academicpages/academicpages.github.io/blob/master/_config.yml), which defines the content in the sidebars and other site-wide features. You will need to replace the default variables with ones about yourself and your site's github repository. The configuration file for the top menu is in [_data/navigation.yml](https://github.com/academicpages/academicpages.github.io/blob/master/_data/navigation.yml). For example, if you don't have a portfolio or blog posts, you can remove those items from that navigation.yml file to remove them from the header. 

Create content & metadata
------
For site content, there is one markdown file for each type of content, which are stored in directories like _publications, _talks, _posts, _teaching, or _pages. For example, each talk is a markdown file in the [_talks directory](https://github.com/academicpages/academicpages.github.io/tree/master/_talks). At the top of each markdown file is structured data in YAML about the talk, which the theme will parse to do lots of cool stuff. The same structured data about a talk is used to generate the list of talks on the [Talks page](https://academicpages.github.io/talks), each [individual page](https://academicpages.github.io/talks/2012-03-01-talk-1) for specific talks, the talks section for the [CV page](https://academicpages.github.io/cv), and the [map of places you've given a talk](https://academicpages.github.io/talkmap.html) (if you run this [python file](https://github.com/academicpages/academicpages.github.io/blob/master/talkmap.py) or [Jupyter notebook](https://github.com/academicpages/academicpages.github.io/blob/master/talkmap.ipynb), which creates the HTML for the map based on the contents of the _talks directory).

**Markdown generator**

I have also created [a set of Jupyter notebooks](https://github.com/academicpages/academicpages.github.io/tree/master/markdown_generator
) that converts a CSV containing structured data about talks or presentations into individual markdown files that will be properly formatted for the Academic Pages template. The sample CSVs in that directory are the ones I used to create my own personal website at stuartgeiger.com. My usual workflow is that I keep a spreadsheet of my publications and talks, then run the code in these notebooks to generate the markdown files, then commit and push them to the GitHub repository.

How to edit your site's GitHub repository
------
Many people use a git client to create files on their local computer and then push them to GitHub's servers. If you are not familiar with git, you can directly edit these configuration and markdown files directly in the github.com interface. Navigate to a file (like [this one](https://github.com/academicpages/academicpages.github.io/blob/master/_talks/2012-03-01-talk-1.md) and click the pencil icon in the top right of the content preview (to the right of the "Raw | Blame | History" buttons). You can delete a file by clicking the trashcan icon to the right of the pencil icon. You can also create new files or upload files by navigating to a directory and clicking the "Create new file" or "Upload files" buttons. 

Example: editing a markdown file for a talk
![Editing a markdown file for a talk](/images/editing-talk.png)

For more info
------
More info about configuring Academic Pages can be found in [the guide](https://academicpages.github.io/markdown/). The [guides for the Minimal Mistakes theme](https://mmistakes.github.io/minimal-mistakes/docs/configuration/) (which this theme was forked from) might also be helpful.
