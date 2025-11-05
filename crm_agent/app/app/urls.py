"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# CRITICAL: Apply OpenAI patch BEFORE any Vanna imports
# This ensures the proxies parameter is handled correctly
from crm_agent.agent.openai_patch import apply_openai_proxies_patch
apply_openai_proxies_patch()

from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from crm_agent.api.health import router as health_router
from crm_agent.api.auth import router as auth_router
from crm_agent.api.leads import router as leads_router
from crm_agent.api.docs import router as docs_router
from crm_agent.api.t2sql import router as t2sql_router
from crm_agent.api.agent import router as agent_router

api = NinjaAPI(title="CRM Agent API")
api.add_router("", health_router)
api.add_router("", auth_router)
api.add_router("", leads_router)
api.add_router("", docs_router)
api.add_router("", t2sql_router)
api.add_router("", agent_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]