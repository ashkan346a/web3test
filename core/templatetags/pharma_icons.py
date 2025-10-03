from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def pharma_icon(icon_name, size='medium', color='primary', bg=False, animation=None, css_class=''):
	"""
	Render a PharmaWeb SVG icon from the inline sprite.

	Usage:
	  {% pharma_icon 'pill-icon' size='large' color='primary' %}
	  {% pharma_icon 'heart-health-icon' bg=True animation='pulse' %}
	"""

	# Size classes
	size_classes = {
		'small': 'pharma-icon--small',
		'medium': '',  # default
		'large': 'pharma-icon--large',
		'xl': 'pharma-icon--xl',
	}

	# Color classes
	color_classes = {
		'primary': 'pharma-icon--primary',
		'secondary': 'pharma-icon--secondary',
		'success': 'pharma-icon--success',
		'warning': 'pharma-icon--warning',
		'danger': 'pharma-icon--danger',
		'info': 'pharma-icon--info',
		'white': 'pharma-icon--white',
		'muted': 'pharma-icon--muted',
	}

	# Animation classes
	animation_classes = {
		'pulse': 'pharma-icon--pulse',
		'bounce': 'pharma-icon--bounce',
		'rotate': 'pharma-icon--rotate',
		'glow': 'pharma-icon--glow',
	}

	classes = ['pharma-icon']

	if size in size_classes and size_classes[size]:
		classes.append(size_classes[size])
	if color in color_classes:
		classes.append(color_classes[color])
	if animation and animation in animation_classes:
		classes.append(animation_classes[animation])
	if bg:
		classes.append('pharma-icon-bg')
		if color in ['primary', 'success', 'warning', 'danger']:
			classes.append(f'pharma-icon-bg--{color}')
	if css_class:
		classes.append(css_class)

	svg_html = f"""
	<svg class="{' '.join(classes)}" aria-hidden="true" focusable="false" role="img">
		<use href="#{icon_name}"></use>
	</svg>
	"""
	return mark_safe(svg_html)


@register.simple_tag
def pharma_feature_card(icon_name, title, description, link_url=None, link_text="بیشتر بدانید"):
	"""Render a feature card with an icon and optional link."""
	link_html = f'<a href="{link_url}" class="btn btn-outline-primary btn-sm mt-2">{link_text}</a>' if link_url else ''
	card_html = f"""
	<div class="pharma-feature-card">
		<svg class="pharma-icon pharma-icon--xl pharma-icon--primary">
			<use href="#{icon_name}"></use>
		</svg>
		<h5 class="fw-bold mb-2">{title}</h5>
		<p class="text-muted mb-3">{description}</p>
		{link_html}
	</div>
	"""
	return mark_safe(card_html)


@register.simple_tag
def pharma_icon_list_item(icon_name, text, color='primary'):
	item_html = f"""
	<li class="pharma-icon-list-item">
		<svg class="pharma-icon pharma-icon--{color}">
			<use href="#{icon_name}"></use>
		</svg>
		<span>{text}</span>
	</li>
	"""
	return mark_safe(item_html)


@register.inclusion_tag('includes/pharma_icons_sprite.html')
def load_pharma_icons():
	"""Inject the SVG sprite once per page."""
	return {}

