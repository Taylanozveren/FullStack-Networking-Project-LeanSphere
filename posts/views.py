from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils.log import logger
from core.utils import generate_explanation
from .models import Post

@login_required
def explain_post(request, post_id):
    """
    Post için AI açıklaması üretir.
    """
    try:
        post = get_object_or_404(Post, id=post_id)
        
        # Post içeriğini logla
        logger.debug(f"Explaining post {post_id}: Title='{post.title}', Content='{post.content[:100]}...'")
        
        # API'yi çağır
        explanation = generate_explanation(f"{post.title} - {post.content}")
        
        # Başarılı sonucu logla
        logger.info(f"Generated explanation for post {post_id}: {explanation[:100]}...")
        
        return JsonResponse({
            'explanation': explanation,
            'post_id': post_id,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error explaining post {post_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': str(e),
            'post_id': post_id,
            'status': 'error'
        }, status=500) 