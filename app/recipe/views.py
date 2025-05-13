"""
Views for the recipe app.
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema, 
    OpenApiParameter,
    OpenApiTypes,)
from rest_framework import (viewsets, mixins, status)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from recipe.serializers import (RecipeSerializer, 
                                RecipeDetailSerializer, 
                                RecipeImageSerializer,
                                TagSerializer,
                                IngredientSerializer)
from core.models import (Recipe, Tag, Ingredient)


@extend_schema_view(
    list=extend_schema(  # Cause we want to extend the schema for list endpoint
        parameters=[
            OpenApiParameter(
                name='tags',
                type=OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter',
            ),
            OpenApiParameter(
                name='ingredients',
                type=OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter',
            ),
        ],
    ),
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for managing recipe APIs."""
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Return recipes for the authenticated user."""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        # adding in a local variable to apply the filters
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        # Very important to return queryset not self.queryset
        return queryset.filter(
            user=self.request.user).distinct().order_by('-id')
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'list':
            return RecipeSerializer
        elif self.action == 'upload_image':
            return RecipeImageSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)
    """
    The @action decorator is used to create custom actions in viewsets.
    By default, it creates a GET endpoint, but you can specify 
    the method(s) to be used. The detail parameter indicates whether the action 
    is for a single object (True) or a list (False).
    The url_path parameter allows you to specify a custom URL for the action.
    The action method should be defined in the viewset class.
    """
    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
Mixins should be passed before GenericViewSet so that the viewset can be 
overriden. Mixins are designed to work with GenericViewSet or GenericAPIView, 
but they require the base class to provide the necessary functionality.
"""


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name='assigned_only',
                type=OpenApiTypes.INT, enum=[0, 1],
                description='Filter by assigned recipes',
            ),
        ],
    ),
)
class BaseRecipeAttrViewSet(mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for recipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return objects for the authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(
            user=self.request.user
            ).distinct().order_by('-name')
    

class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database."""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
