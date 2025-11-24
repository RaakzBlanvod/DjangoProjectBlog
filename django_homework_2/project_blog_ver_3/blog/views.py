from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView
)

from .forms import RegistrationForm, UserUpdateForm, PostForm, CommentForm
from .models import Post, Category, Comment
from blogicum.constants import MAX_POSTS_ON_MAIN

User = get_user_model()


def index(request):
    template = 'blog/index.html'
    post_list = Post.pub_posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects, pk=post_id)
    if post.author != request.user:
        post = get_object_or_404(Post.pub_posts, pk=post_id)
    
    comments = post.comments.select_related('author')
    form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category.objects.filter(is_published=True),
        slug=category_slug
    )
    post_list = Post.pub_posts.filter(category=category)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template, context)


class UserRegistrationView(CreateView):
    form_class = RegistrationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('index')


class UserProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        posts = user.posts.select_related('category', 'location')
        
        if self.request.user != user:
            posts = posts.filter(is_published=True, pub_date__lte=timezone.now())
        
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['page_obj'] = page_obj
        return context


class UserProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user_form.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def test_func(self):
        user = self.get_object()
        return self.request.user == user

    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'username': self.object.username})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
    
    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'username': self.request.user.username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    
    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    
    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author
    
    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/detail.html'
    
    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author
    
    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'post_id': self.kwargs['post_id']})

def get_categories(request):
    categories = Category.objects.filter(is_published=True)
    return {'all_categories': categories}