from django.test import TestCase
from django.urls import reverse
from .models import User, Conversation, Message, Item

# Create your tests here.

class MessageTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.item = Item.objects.create(title='Test Item', description='Description', price=10.00, posted_by=self.user1)
        self.conversation = Conversation.objects.create(buyer=self.user1, seller=self.user2, item=self.item)

    def test_send_message(self):
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('send_message', kwargs={'conversation_id': self.conversation.id}), {'content': 'Hello!'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().content, 'Hello!')
        self.assertRedirects(response, reverse('conversation-detail', kwargs={'pk': self.conversation.id}))

    def test_message_list_view(self):
        self.client.login(username='user1', password='password')
        response = self.client.get(reverse('message_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'message_list.html')
        self.assertContains(response, 'Test Item')  # Check for the item in the response
        self.assertContains(response, 'Hello!')  # Check for the message in the response
        self.assertContains(response, 'Your Messages')  # Check for a header or specific text in the template
