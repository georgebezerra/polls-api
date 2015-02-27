import json
from django.views.generic import View

from polls.models import Question, Choice, Vote

from polls.resource import Resource, CollectionResource, SingleObjectMixin


class RootResource(Resource):
    uri = '/'

    def get_relations(self):
        return {
            'questions': QuestionCollectionResource(),
        }

    def can_embed(self, relation):
        return False


class QuestionResource(Resource, SingleObjectMixin):
    model = Question

    def get_uri(self):
        return '/questions/{}'.format(self.get_object().pk)

    def get_attributes(self):
        question = self.get_object()

        return {
            'question': question.question_text,
            'published_at': question.published_at.isoformat(),
        }

    def get_relations(self):
        choices = self.get_object().choice_set.all()

        def choice_resource(choice):
            resource = ChoiceResource()
            resource.obj = choice
            return resource

        return {
            'choices': map(choice_resource, choices),
        }


class ChoiceResource(Resource, SingleObjectMixin):
    model = Choice

    def get_uri(self):
        choice = self.get_object()
        return '/questions/{}/choices/{}'.format(choice.question.pk, choice.pk)

    def get_attributes(self):
        choice = self.get_object()

        return {
            'choice': choice.choice_text,
            'votes': choice.votes,
        }

    def post(self, request, *args, **kwargs):
        choice = self.get_object()
        Vote(choice=choice).save()
        response = self.get(request)
        response.status_code = 201
        response['Location'] = self.get_uri()
        return response

class QuestionCollectionResource(CollectionResource):
    resource = QuestionResource
    model = Question
    relation = 'questions'
    uri = '/questions'

    def post(self, request):
        body = json.loads(request.body)
        question_text = body.get('question')
        choices = body.get('choices')

        if not question_text or not isinstance(choices, list):
            return HttpResponse(status=400)

        question = Question(question_text=question_text)
        question.save()
        for choice_text in choices:
            Choice(question=question, choice_text=choice_text).save()

        resource = self.resource()
        resource.obj = question
        response = resource.get(request)
        response.status_code = 201
        response['Location'] = resource.get_uri()
        return response

