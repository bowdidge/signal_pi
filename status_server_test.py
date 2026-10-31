#!/usr/bin/env python
#
# Unit tests for StatusTracker and HTTP status server.
#

import json
import unittest

try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error

import layout
import mock_port_expander
import status_server
import status_tracker



class StatusTrackerTest(unittest.TestCase):
    """Unit tests for StatusTracker storage and event tracking."""

    def testInitializeAndRecord(self):
        tracker = status_tracker.StatusTracker()
        tracker.initialize_names(['BLOCK_1', 'SW_GLEN_W'], ['W1R', 'W1G'])

        snapshot = tracker.get_snapshot()
        self.assertIn('BLOCK_1', snapshot['inputs'])
        self.assertIn('W1R', snapshot['outputs'])
        self.assertFalse(snapshot['inputs']['BLOCK_1'])
        self.assertEqual(len(snapshot['recent_changes']), 0)

        # Record input change
        tracker.record_change('BLOCK_1', True, is_input=True)
        snapshot = tracker.get_snapshot()
        self.assertTrue(snapshot['inputs']['BLOCK_1'])
        self.assertEqual(len(snapshot['recent_changes']), 1)
        self.assertEqual(snapshot['recent_changes'][0]['name'], 'BLOCK_1')
        self.assertEqual(snapshot['recent_changes'][0]['type'], 'input')
        self.assertTrue(snapshot['recent_changes'][0]['value'])

        # Verify pending LCD message was set for Solution 2 single-threaded consumption
        msg = tracker.pop_pending_lcd_message()
        self.assertIsNotNone(msg)
        self.assertIn('BLOCK_1', msg[0])
        # Calling again should return None until next change
        self.assertIsNone(tracker.pop_pending_lcd_message())

        # Redundant recording with same value should not create duplicate events
        tracker.record_change('BLOCK_1', True, is_input=True)
        self.assertEqual(len(tracker.get_snapshot()['recent_changes']), 1)
        self.assertIsNone(tracker.pop_pending_lcd_message())

        # Record output change
        tracker.record_change('W1R', True, is_input=False)
        snapshot = tracker.get_snapshot()
        self.assertTrue(snapshot['outputs']['W1R'])
        self.assertEqual(len(snapshot['recent_changes']), 2)
        self.assertEqual(snapshot['recent_changes'][0]['name'], 'W1R')
        self.assertEqual(snapshot['recent_changes'][0]['type'], 'output')


class StatusServerHttpTest(unittest.TestCase):
    """Unit tests for HTTP server endpoints."""

    def setUp(self):
        self.tracker = status_tracker.StatusTracker()
        self.tracker.initialize_names(['BLOCK_1'], ['W1R', 'W1G'])
        self.tracker.record_change('BLOCK_1', True, is_input=True)
        self.tracker.record_change('W1R', True, is_input=False)

        # Port 0 instructs the OS to bind to a dynamic available ephemeral port
        self.server, self.thread = status_server.start_status_server(
            self.tracker, host='127.0.0.1', port=0
        )
        self.port = self.server.server_address[1]

    def tearDown(self):
        status_server.stop_status_server(self.server)

    def testGetApiStatus(self):
        url = 'http://127.0.0.1:%d/api/status' % self.port
        req = urllib_request.Request(url)
        resp = urllib_request.urlopen(req, timeout=3.0)
        try:
            self.assertEqual(resp.getcode(), 200)
            self.assertIn('application/json', str(resp.info()))
            data = json.loads(resp.read().decode('utf-8'))

            self.assertIn('inputs', data)
            self.assertIn('outputs', data)
            self.assertIn('recent_changes', data)
            self.assertTrue(data['inputs']['BLOCK_1'])
            self.assertTrue(data['outputs']['W1R'])
            self.assertEqual(len(data['recent_changes']), 2)
        finally:
            resp.close()

    def testGetHtmlDashboard(self):
        url = 'http://127.0.0.1:%d/' % self.port
        req = urllib_request.Request(url)
        resp = urllib_request.urlopen(req, timeout=3.0)
        try:
            self.assertEqual(resp.getcode(), 200)
            self.assertIn('text/html', str(resp.info()))
            body = resp.read().decode('utf-8')
            self.assertIn('Vasona Branch', body)
            self.assertIn('/api/status', body)
        finally:
            resp.close()

    def testGetNotFound(self):
        url = 'http://127.0.0.1:%d/nonexistent' % self.port
        try:
            resp = urllib_request.urlopen(url, timeout=3.0)
            self.assertEqual(resp.getcode(), 404)
            resp.close()
        except urllib_error.HTTPError as err:
            self.assertEqual(err.code, 404)


class LayoutIntegrationWithTrackerTest(unittest.TestCase):
    """Verify that layout.setup_layout integrates cleanly with StatusTracker."""

    def testLayoutUpdatesTrackerAndLcdQueue(self):
        tracker = status_tracker.StatusTracker()
        logic_engine, expanders = layout.setup_layout(
            mock_port_expander.PortExpander, status_tracker=tracker
        )

        snapshot = tracker.get_snapshot()
        self.assertIn('BLOCK_1', snapshot['inputs'])
        self.assertIn('W1R', snapshot['outputs'])

        # Drop line 0 (BLOCK_1) to trigger state changes
        expanders[0].mock_set_input(0, False)
        logic_engine.poll()

        snapshot = tracker.get_snapshot()
        self.assertTrue(snapshot['inputs']['BLOCK_1'])
        self.assertTrue(snapshot['outputs']['W1R'])

        # Solution 2: Verify message is queued for the main thread to service sequentially
        pending_msg = tracker.pop_pending_lcd_message()
        self.assertIsNotNone(pending_msg)
        self.assertIn('OUT:', pending_msg[0])


if __name__ == '__main__':
    unittest.main()
