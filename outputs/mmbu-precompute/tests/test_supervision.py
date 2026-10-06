import unittest


def api():
    from mmbu_prep.supervision import assistant_labels,pad_supervised_batch
    return assistant_labels,pad_supervised_batch


class SupervisionTests(unittest.TestCase):
    def test_only_exact_native_suffix_gets_loss(self):
        labels,_=api()
        self.assertEqual(labels([1,99,2],[1,99,2,5,6,7],forbidden_target_ids={99},max_length=8),[-100,-100,-100,5,6,7])

    def test_thinking_prefix_mismatch_never_guesses_target_boundary(self):
        labels,_=api()
        with self.assertRaises(ValueError):labels([1,2,3],[1,2,8,9],forbidden_target_ids=set(),max_length=10)

    def test_empty_targets_oversize_and_special_target_tokens_rejected(self):
        labels,_=api()
        for full,maximum in [([1,2],8),([1,2,99],8),([1,2,3,4],3)]:
            with self.assertRaises(ValueError):labels([1,2],full,forbidden_target_ids={99},max_length=maximum)
        for prompt in ([],[True],[-1],[1.0]):
            with self.assertRaises(ValueError):labels(prompt,[1,2,3],forbidden_target_ids=set(),max_length=8)

    def test_batch_padding_masks_padding_but_retains_supervised_eos(self):
        _,pad=api()
        out=pad([{'input_ids':[1,2,3],'labels':[-100,2,3]}, {'input_ids':[1,7],'labels':[-100,7]}],pad_token_id=0,max_length=4,pad_to_multiple_of=4)
        self.assertEqual(out['input_ids'],[[1,2,3,0],[1,7,0,0]])
        self.assertEqual(out['labels'],[[-100,2,3,-100],[-100,7,-100,-100]])
        self.assertEqual(out['attention_mask'],[[1,1,1,0],[1,1,0,0]])
        self.assertEqual(out['supervised_tokens'],3)

    def test_inconsistent_labels_missing_supervision_and_rounding_over_cap_rejected(self):
        _,pad=api()
        bad=[{'input_ids':[1,2],'labels':[-100]}, {'input_ids':[1,2],'labels':[-100,9]}, {'input_ids':[1,2],'labels':[-100,-100]}]
        for row in bad:
            with self.assertRaises(ValueError):pad([row],pad_token_id=0,max_length=8)
        with self.assertRaises(ValueError):pad([{'input_ids':[1,2,3],'labels':[-100,2,3]}],pad_token_id=0,max_length=3,pad_to_multiple_of=4)

    def test_unmasked_first_position_cannot_count_as_causal_target(self):
        _,pad=api()
        with self.assertRaises(ValueError):pad([{'input_ids':[7,9],'labels':[7,-100]}],pad_token_id=0,max_length=2)
        with self.assertRaises(ValueError):pad([{'input_ids':[7,9],'labels':[7,9]}],pad_token_id=0,max_length=2)
