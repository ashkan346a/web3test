from django.urls import path, re_path
from . import views
from . import auth_views

import importlib, sys

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("guide/", views.GuideView.as_view(), name="guide"),
    path("support/", views.SupportView.as_view(), name="support"),

    path("buy-medicine/", views.buy_medicine, name="buy_medicine"),
    path("item/<str:item_id>/", views.medicine_detail, name="medicine_detail"),

    path("cart/", views.cart, name="cart"),
    path("cart/view/", views.view_cart, name="cart_view"),
    path("cart/add/<str:item_id>/", auth_views.cart_add, name="cart_add"),
    path("cart/remove/<str:item_id>/", views.cart_remove, name="cart_remove"),
    path("cart/clear/", views.cart_clear, name="cart_clear"),
    # single route that accepts an optional item_id (so templates can reverse with or without an arg)
    re_path(r'^cart/update(?:/(?P<item_id>[^/]+))?/$', views.cart_update, name='cart_update'),

    path("checkout/", views.checkout, name="checkout"),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('order-success/', views.order_success, name='order_success'),
    path("payment/<uuid:order_id>/", views.payment, name="payment"),

    path("orders/", views.OrderHistoryView.as_view(), name="order_history"),

    path("login/", views.login_view, name="login"),
    path("login/", views.login_view, name="login_view"),
    path("register/", views.register_view, name="register_view"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("logout/", views.LogoutView.as_view(), name="logout_view"),

    path("accounts/login/", views.login_view, name="accounts_login"),

    path("profile/", views.profile, name="profile"),

    path("lang/", views.ChangeLanguageView.as_view(), name="set_language"),

    path("admin-panel/", views.AdminPanelView.as_view(), name="admin_panel"),
    path("admin-panel/export-csv/", views.admin_export_orders_csv, name="admin_export_orders_csv"),
    path("support/console/", views.telegram_chat_console, name="agent_console"),
    path("support/console/legacy/", views.agent_console_legacy, name="agent_console_legacy"),
    path("support/console/old/", views.agent_console, name="agent_console_old"),
    

    path("api/search/", views.api_search, name="api_search"),
    path("api/chat/rooms/", views.api_chat_rooms, name="api_chat_rooms"),
    path("api/chat/messages/<int:room_id>/", views.api_chat_messages, name="api_chat_messages"),
    path("api/chat/clear-messages/<int:room_id>/", views.api_clear_chat_messages, name="api_clear_chat_messages"),
    path("api/chat/delete-chat/<int:room_id>/", views.api_delete_chat, name="api_delete_chat"),
    path("api/chat/block-user/<int:room_id>/", views.api_block_user, name="api_block_user"),
    path("api/chat/unblock-user/<int:room_id>/", views.api_unblock_user, name="api_unblock_user"),

    path('password-reset/', auth_views.password_reset, name='password_reset'),
    path('password-reset/done/', auth_views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/<str:uidb64>/<str:token>/', auth_views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.password_reset_complete, name='password_reset_complete'),

    path('api/rates/', views.api_live_rates if hasattr(views, 'api_live_rates') else views.get_exchange_rates, name='api_live_rates'),
    # alias used by templates / scripts
    path('api/live_rates/', views.api_live_rates if hasattr(views, 'api_live_rates') else views.get_exchange_rates, name='api_live_rates_live'),
    path('api/check_payment/', views.api_check_payment if hasattr(views, 'api_check_payment') else views.api_check_payment, name='api_check_payment'),
    path('api/payment/irr/', views.api_payment_irr, name='api_payment_irr'),
]