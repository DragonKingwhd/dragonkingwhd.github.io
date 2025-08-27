---
layout: default
title: 关于我
permalink: /about/
---

<section class="about-header">
    <div class="container">
        <div class="about-intro">
            <div class="about-avatar">
                <img src="{{ '/assets/images/avatar.jpg' | relative_url }}" alt="我的头像" class="avatar">
            </div>
            <div class="about-text">
                <h1>关于我</h1>
                <p class="lead">你好！我是一名热爱技术的开发者</p>
                <div class="social-links">
                    {% if site.social.github %}
                    <a href="https://github.com/{{ site.social.github }}" target="_blank">
                        <i class="fab fa-github"></i>
                    </a>
                    {% endif %}
                    
                    {% if site.social.twitter %}
                    <a href="https://twitter.com/{{ site.social.twitter }}" target="_blank">
                        <i class="fab fa-twitter"></i>
                    </a>
                    {% endif %}
                    
                    {% if site.social.linkedin %}
                    <a href="https://linkedin.com/in/{{ site.social.linkedin }}" target="_blank">
                        <i class="fab fa-linkedin"></i>
                    </a>
                    {% endif %}
                    
                    {% if site.social.email %}
                    <a href="mailto:{{ site.social.email }}">
                        <i class="fas fa-envelope"></i>
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</section>

<section class="about-content">
    <div class="container">
        <div class="about-sections">
            <div class="about-section">
                <h2><i class="fas fa-user"></i> 个人简介</h2>
                <p>
                    我是一名充满热情的程序员，喜欢探索新技术，解决有挑战性的问题。
                    在这个博客里，我会分享我的学习经验、技术心得和一些有趣的项目。
                </p>
                <p>
                    我相信技术可以改变世界，也相信通过分享知识可以帮助更多的人成长。
                    如果你对我的文章或项目有任何问题或建议，欢迎随时与我联系！
                </p>
            </div>

            <div class="about-section">
                <h2><i class="fas fa-code"></i> 技能专长</h2>
                <div class="skills-grid">
                    <div class="skill-category">
                        <h3>前端开发</h3>
                        <div class="skills">
                            <span class="skill">HTML/CSS</span>
                            <span class="skill">JavaScript</span>
                            <span class="skill">React</span>
                            <span class="skill">Vue.js</span>
                        </div>
                    </div>
                    
                    <div class="skill-category">
                        <h3>后端开发</h3>
                        <div class="skills">
                            <span class="skill">Python</span>
                            <span class="skill">Node.js</span>
                            <span class="skill">Java</span>
                            <span class="skill">数据库</span>
                        </div>
                    </div>
                    
                    <div class="skill-category">
                        <h3>工具与框架</h3>
                        <div class="skills">
                            <span class="skill">Git</span>
                            <span class="skill">Docker</span>
                            <span class="skill">Linux</span>
                            <span class="skill">AWS</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="about-section">
                <h2><i class="fas fa-heart"></i> 兴趣爱好</h2>
                <div class="interests">
                    <div class="interest">
                        <i class="fas fa-laptop-code"></i>
                        <h4>编程</h4>
                        <p>探索新的编程语言和技术框架</p>
                    </div>
                    
                    <div class="interest">
                        <i class="fas fa-book"></i>
                        <h4>学习</h4>
                        <p>持续学习新技术，保持技术敏感度</p>
                    </div>
                    
                    <div class="interest">
                        <i class="fas fa-users"></i>
                        <h4>开源</h4>
                        <p>参与开源项目，为社区做贡献</p>
                    </div>
                    
                    <div class="interest">
                        <i class="fas fa-pen"></i>
                        <h4>写作</h4>
                        <p>分享技术文章和学习心得</p>
                    </div>
                </div>
            </div>

            <div class="about-section">
                <h2><i class="fas fa-envelope"></i> 联系我</h2>
                <p>
                    如果你想与我交流技术问题，讨论项目合作，或者只是想打个招呼，
                    都可以通过以下方式联系我：
                </p>
                <div class="contact-info">
                    {% if site.social.email %}
                    <div class="contact-item">
                        <i class="fas fa-envelope"></i>
                        <a href="mailto:{{ site.social.email }}">{{ site.social.email }}</a>
                    </div>
                    {% endif %}
                    
                    {% if site.social.github %}
                    <div class="contact-item">
                        <i class="fab fa-github"></i>
                        <a href="https://github.com/{{ site.social.github }}" target="_blank">
                            github.com/{{ site.social.github }}
                        </a>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</section>