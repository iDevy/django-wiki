from django.views.generic.base import TemplateResponseMixin
from wiki.models import Comment
from wiki.forms import CommentForm
from wiki.core.plugins import registry
from wiki.conf import settings
from django.shortcuts import redirect


class ArticleMixin(TemplateResponseMixin):
    """A mixin that receives an article object as a parameter (usually from a wiki
    decorator) and puts this information as an instance attribute and in the
    template context."""

    def dispatch(self, request, article, *args, **kwargs):

        self.urlpath = kwargs.pop('urlpath', None)
        self.article = article
        self.children_slice = []
        
        if settings.SHOW_MAX_CHILDREN > 0:
            try:
                for child in self.article.get_children(max_num=settings.SHOW_MAX_CHILDREN + 1,
                                                       articles__article__current_revision__deleted=False,
                                                       user_can_read=request.user):
                    self.children_slice.append(child)
            except AttributeError, e:
                raise Exception("Attribute error most likely caused by wrong MPTT version. Use 0.5.3+.\n\n" + str(e))
        return super(ArticleMixin, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Go to the article view page when the article has been saved"""
        if self.urlpath:
            return redirect("wiki:get", path=self.urlpath.path)
        return redirect('wiki:get', article_id=self.article.id)

    def get_context_data(self, **kwargs):
        kwargs['urlpath'] = self.urlpath
        kwargs['article'] = self.article
        kwargs['article_tabs'] = registry.get_article_tabs()
        kwargs['children_slice'] = self.children_slice[:20]
        kwargs['children_slice_more'] = len(self.children_slice) > 20
        kwargs['plugins'] = registry.get_plugins()

        # team112 - comment management
        kwargs['can_read_comment'] = self.article.can_read_comment(self.request.user)
        kwargs['can_delete_comment'] = self.article.can_delete_comment(self.request.user)
        kwargs['can_comment'] = self.article.can_comment(self.request.user)
        kwargs['commentform'] = CommentForm
        kwargs['comments'] = Comment.objects.get_comments(self.article)

        return kwargs
