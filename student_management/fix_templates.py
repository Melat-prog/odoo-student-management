import re

with open('/home/melat/odoo18-dev/student_management/views/website_templates.xml', 'r') as f:
    content = f.read()

head_block = """
            <t t-set="head">
                <link rel="preconnect" href="https://fonts.googleapis.com"/>
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="crossorigin"/>
                <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&amp;display=swap" rel="stylesheet"/>
                <style>
                    body, #wrapwrap {
                        background-color: #fcfbf9 !important;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                        color: #1c1c1c !important;
                    }
                    .amherst-heading {
                        font-family: 'Playfair Display', Georgia, serif !important;
                        font-weight: 800 !important;
                        letter-spacing: -0.02em !important;
                        text-transform: uppercase !important;
                        color: #0f0f0f !important;
                    }
                    .amherst-subheading {
                        font-family: 'Playfair Display', Georgia, serif !important;
                        font-style: italic !important;
                        color: #4a4a4a !important;
                    }
                    .btn-amherst {
                        background-color: #4a0e17 !important;
                        color: #ffffff !important;
                        border-radius: 0px !important;
                        padding: 14px 32px !important;
                        font-size: 0.85rem !important;
                        letter-spacing: 2px !important;
                        text-transform: uppercase !important;
                        font-weight: 700 !important;
                        border: none !important;
                    }
                    .amherst-hero-banner {
                        background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), url('https://images.unsplash.com/photo-1541829070764-84a7d30dd3f3?q=80&amp;w=2000&amp;auto=format&amp;fit=crop') center/cover no-repeat !important;
                        min-height: 480px;
                    }
                    .amherst-border-right { border-right: 1px solid #e0dad1 !important; }
                    .amherst-border-bottom { border-bottom: 1px solid #e0dad1 !important; }
                </style>
            </t>"""

content = content.replace('<t t-call="website.layout">', '<t t-call="website.layout">' + head_block)

new_templates = """
    <!-- ABOUT US PAGE -->
    <template id="about_us_page" name="About Us">
        <t t-call="website.layout">
            <div class="amherst-hero-banner d-flex align-items-center justify-content-center text-center">
                <h1 class="text-white amherst-heading" style="font-size: 4rem;">About Us</h1>
            </div>
            <div class="container py-5">
                <div class="row">
                    <div class="col-md-8 offset-md-2 text-center">
                        <h2 class="amherst-heading mb-4">Our Heritage</h2>
                        <p class="lead">Founded on principles of academic excellence and intellectual freedom, we are committed to shaping the minds of tomorrow through rigorous inquiry and comprehensive education.</p>
                    </div>
                </div>
            </div>
        </t>
    </template>

    <!-- ACADEMICS PAGE (Replaces school_programs) -->
    <template id="academics_page" name="Academics">
        <t t-call="website.layout">
            <div class="amherst-hero-banner d-flex align-items-center justify-content-center text-center" style="background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('https://images.unsplash.com/photo-1497633762265-9d179a990aa6?q=80&amp;w=2000&amp;auto=format&amp;fit=crop') center/cover !important;">
                <h1 class="text-white amherst-heading" style="font-size: 4rem;">Academics</h1>
            </div>
            <div class="container py-5">
                <div class="row">
                    <t t-foreach="courses" t-as="course">
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div class="card h-100 shadow-sm border-0 rounded-0 amherst-border-bottom">
                                <div class="card-body p-4">
                                    <h4 class="amherst-heading mb-3"><t t-esc="course.name"/></h4>
                                    <p class="text-muted"><t t-esc="course.description"/></p>
                                </div>
                                <div class="card-footer bg-white border-0 pt-0 pb-4">
                                    <a href="/school/admissions" class="btn btn-amherst w-100">Apply Now</a>
                                </div>
                            </div>
                        </div>
                    </t>
                </div>
            </div>
        </t>
    </template>

    <!-- RESEARCH PAGE -->
    <template id="research_page" name="Research">
        <t t-call="website.layout">
            <div class="amherst-hero-banner d-flex align-items-center justify-content-center text-center" style="background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('https://images.unsplash.com/photo-1532094349884-543bc11b234d?q=80&amp;w=2000&amp;auto=format&amp;fit=crop') center/cover !important;">
                <h1 class="text-white amherst-heading" style="font-size: 4rem;">Research</h1>
            </div>
            <div class="container py-5">
                <div class="row">
                    <div class="col-md-12 text-center">
                        <h2 class="amherst-heading mb-4">Pushing Boundaries</h2>
                        <p class="lead">Our research initiatives are driven by a passion for discovery and a commitment to addressing the world's most pressing challenges.</p>
                    </div>
                </div>
            </div>
        </t>
    </template>

    <!-- CAMPUS LIFE PAGE -->
    <template id="campus_life_page" name="Campus Life">
        <t t-call="website.layout">
            <div class="amherst-hero-banner d-flex align-items-center justify-content-center text-center" style="background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&amp;w=2000&amp;auto=format&amp;fit=crop') center/cover !important;">
                <h1 class="text-white amherst-heading" style="font-size: 4rem;">Campus Life</h1>
            </div>
            <div class="container py-5">
                <div class="row">
                    <div class="col-md-12 text-center">
                        <h2 class="amherst-heading mb-4">A Vibrant Community</h2>
                        <p class="lead">Experience a dynamic campus environment that fosters creativity, collaboration, and personal growth.</p>
                    </div>
                </div>
            </div>
        </t>
    </template>

    <!-- CONTACT PAGE -->
    <template id="contact_page" name="Contact">
        <t t-call="website.layout">
            <div class="amherst-hero-banner d-flex align-items-center justify-content-center text-center" style="background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&amp;w=2000&amp;auto=format&amp;fit=crop') center/cover !important;">
                <h1 class="text-white amherst-heading" style="font-size: 4rem;">Contact Us</h1>
            </div>
            <div class="container py-5">
                <div class="row">
                    <div class="col-md-6 offset-md-3 text-center">
                        <h2 class="amherst-heading mb-4">Get in Touch</h2>
                        <p class="lead mb-5">We are here to answer your questions and provide the information you need.</p>
                        <a href="mailto:admissions@nextgen.edu" class="btn btn-amherst">Email Admissions</a>
                    </div>
                </div>
            </div>
        </t>
    </template>
</odoo>
"""

content = content.replace('</odoo>', new_templates)

with open('/home/melat/odoo18-dev/student_management/views/website_templates.xml', 'w') as f:
    f.write(content)
