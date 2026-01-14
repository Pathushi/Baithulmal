from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name="index.html"), name='home'),
    path('about-cbf.html', TemplateView.as_view(template_name="about-cbf.html"), name='about_cbf'),
    path('about-zakat.html', TemplateView.as_view(template_name="about-zakat.html"), name='about_zakat'),
    path('projects.html', TemplateView.as_view(template_name="projects.html"), name='projects'),
    path('gallery.html', TemplateView.as_view(template_name="gallery.html"), name='gallery'),
    path('contact.html', TemplateView.as_view(template_name="contact.html"), name='contact'),
    path('donate.html', TemplateView.as_view(template_name="donate.html"), name='donate'),
    path('news.html', TemplateView.as_view(template_name="news.html"), name='news'),
    path('partners.html', TemplateView.as_view(template_name="partners.html"), name='partners'),
    path('calender.html', TemplateView.as_view(template_name="calender.html"), name='calender'),
    path('payments/', include('payments.urls')),
]
