# -*- test-case-name: vumi.demos.tests.test_decisiontree -*-

"""Basic tools for building a vumi ApplicationWorker."""

import json

from twisted.internet.defer import inlineCallbacks
from twisted.python import log

from vumi.errors import ConfigError
from vumi.message import TransportUserMessage
from vumi.session import getVumiSession, delVumiSession, TraversedDecisionTree
from vumi.application import ApplicationWorker


SESSION_NEW = TransportUserMessage.SESSION_NEW
SESSION_CLOSE = TransportUserMessage.SESSION_CLOSE
SESSION_RESUME = TransportUserMessage.SESSION_RESUME


class DecisionTreeWorker(ApplicationWorker):

    @inlineCallbacks
    def startWorker(self):
        yield super(DecisionTreeWorker, self).startWorker()

    @inlineCallbacks
    def stopWorker(self):
        yield super(DecisionTreeWorker, self).stopWorker()

    def consume_user_message(self, msg):
        try:
            response = ''
            continue_session = False
            if True:
                if not self.yaml_template:
                    raise Exception("yaml_template is missing")
                sess = self.get_session(msg.user())
                if not sess.get_decision_tree().is_started():
                    # TODO check this corresponds to session_event = new
                    sess.get_decision_tree().start()
                    response += sess.get_decision_tree().question()
                    continue_session = True
                else:
                    # TODO check this corresponds to session_event = resume
                    sess.get_decision_tree().answer(msg.payload['content'])
                    if not sess.get_decision_tree().is_completed():
                        response += sess.get_decision_tree().question()
                        continue_session = True
                    response += sess.get_decision_tree().finish() or ''
                    if sess.get_decision_tree().is_completed():
                        self.post_result(json.dumps(
                            sess.get_decision_tree().get_data()))
                        sess.delete()
                sess.save()
        except Exception, e:
            print e
        self.reply_to(msg, response, continue_session)

    def set_yaml_template(self, yaml_template):
        self.yaml_template = yaml_template

    def set_data_url(self, data_source):
        self.data_url = data_source

    def set_post_url(self, post_source):
        self.post_url = post_source

    def post_result(self, result):
        # TODO need actual post but
        # just need this to override in testing for now
        pass

    def call_for_json(self):
        # TODO need actual retrieval but
        # just need this to override in testing for now
        return '{}'

    def get_session(self, MSISDN):
        sess = getVumiSession(self.r_server,
                self.transport_name + '.' + MSISDN)
        if not sess.get_decision_tree():
            sess.set_decision_tree(self.setup_new_decision_tree(MSISDN))
        return sess

    def del_session(self, MSISDN):
        return delVumiSession(self.r_server, MSISDN)

    def setup_new_decision_tree(self, MSISDN, **kwargs):
        decision_tree = TraversedDecisionTree()
        yaml_template = self.yaml_template
        decision_tree.load_yaml_template(yaml_template)
        self.set_data_url(decision_tree.get_data_source())
        self.set_post_url(decision_tree.get_post_source())
        if self.data_url.get('url'):
            json_string = self.call_for_json()
            decision_tree.load_json_data(json_string)
        else:
            decision_tree.load_dummy_data()
        return decision_tree