#!/bin/bash
# Railway.com Deployment Script

echo "🚀 Starting Railway Deployment for PharmaWeb SEO..."

# 1. Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 2. Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# 3. Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# 4. Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        phone='+1234567890',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print('✅ Superuser created')
else:
    print('ℹ️ Superuser already exists')
"

# 5. Submit sitemap to search engines (if in production)
if [ "$RAILWAY_ENVIRONMENT_NAME" = "production" ]; then
    echo "🗺️ Submitting sitemap to search engines..."
    python manage.py submit_sitemap --ping-google --submit-bing || echo "⚠️ Sitemap submission failed (normal on first deploy)"
fi

echo "✅ Railway deployment completed successfully!"
echo "🌐 Your site should be available at: $SITE_URL"
echo "📊 Don't forget to:"
echo "   - Set up Google Search Console"
echo "   - Add Google Analytics"
echo "   - Configure environment variables in Railway"