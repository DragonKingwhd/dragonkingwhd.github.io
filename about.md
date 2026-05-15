---
layout: default
title: 关于我
permalink: /about/
---

<style>
.about-header { margin-bottom: 2.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border); }
.about-header .container { padding: 0; max-width: none; margin: 0; }
.about-intro { display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap; }
.avatar-fallback {
    width: 84px; height: 84px;
    border-radius: 50%;
    background: var(--accent-soft);
    border: 1px solid var(--accent-border);
    color: var(--accent);
    font-family: var(--font-sans);
    font-weight: 600;
    font-size: 1.6rem;
    letter-spacing: 0.04em;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.about-text h1 { margin: 0 0 0.45rem; }
.about-text .lead { color: var(--text-soft); margin: 0 0 0.75rem; }
.about-text .social-links { display: flex; gap: 0.75rem; }
.about-text .social-links a {
    width: 34px; height: 34px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: var(--text-soft);
    transition: all 0.15s ease;
}
.about-text .social-links a:hover { color: var(--accent); border-color: var(--accent); }

.about-section { margin-bottom: 2.5rem; }
.about-section h2 {
    display: flex; align-items: center; gap: 0.5rem;
    border: none; padding: 0; margin-top: 0;
    font-size: 1.15rem;
}
.about-section h2 i { color: var(--accent); font-size: 0.95em; }
.skills-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; }
.skill-category h3 { font-size: 0.95rem; margin: 0 0 0.5rem; }
.skills { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.skill {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    background: var(--accent-soft);
    color: var(--accent);
    border: 1px solid var(--accent-border);
    padding: 0.18rem 0.6rem;
    border-radius: 3px;
}
.interests {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
}
.interest {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    background: var(--bg-soft);
}
.interest i { color: var(--accent); font-size: 1.2rem; margin-bottom: 0.45rem; display: block; }
.interest h4 { margin: 0 0 0.3rem; font-size: 0.95rem; }
.interest p { color: var(--text-soft); font-size: 0.85rem; margin: 0; }
.contact-info { display: flex; flex-direction: column; gap: 0.5rem; }
.contact-item { display: flex; align-items: center; gap: 0.6rem; font-family: var(--font-mono); font-size: 0.88rem; }
.contact-item i { color: var(--accent); width: 1.1em; }
.contact-item a { color: var(--text); border-bottom: 1px dotted var(--border); }
.contact-item a:hover { color: var(--accent); border-color: var(--accent); }
</style>

<div class="content-wrap">

<section class="about-header">
    <div class="container">
        <div class="about-intro">
            <div class="about-avatar avatar-fallback" aria-label="Harry Wang">HW</div>
            <div class="about-text">
                <h1>关于我</h1>
                <p class="lead">你好！我是一名机器人与机械工程方向的研究者和开发者</p>
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
                    我是一名机器人与机械工程方向的研究者，专注于强化学习、仿真与控制系统。
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
                        <h3>机器人与控制</h3>
                        <div class="skills">
                            <span class="skill">机器人学</span>
                            <span class="skill">强化学习</span>
                            <span class="skill">控制系统</span>
                            <span class="skill">机械工程</span>
                        </div>
                    </div>

                    <div class="skill-category">
                        <h3>编程语言</h3>
                        <div class="skills">
                            <span class="skill">Python</span>
                            <span class="skill">C/C++</span>
                            <span class="skill">MATLAB</span>
                            <span class="skill">JavaScript</span>
                        </div>
                    </div>

                    <div class="skill-category">
                        <h3>仿真与工具</h3>
                        <div class="skills">
                            <span class="skill">Isaac Sim</span>
                            <span class="skill">MuJoCo</span>
                            <span class="skill">SolidWorks</span>
                            <span class="skill">Git/Linux</span>
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
</div>
