"""Token-boundary checks for provisional supervised examples; no trainer/model."""


def _ids(values,name):
    if not isinstance(values,list) or not values or any(type(x) is not int or x<0 for x in values):
        raise ValueError(name+' must be a nonempty list of nonnegative integer token IDs')


def assistant_labels(prompt_ids, full_ids, *, forbidden_target_ids, max_length):
    """Mask a verified native prompt prefix, supervise complete native suffix.

    Caller must generate both sequences with identical image and processor
    settings and an explicit assistant target. A mismatch is never repaired by
    searching for a role marker or guessing a common-prefix boundary.
    """
    _ids(prompt_ids,'prompt_ids');_ids(full_ids,'full_ids')
    if type(max_length) is not int or max_length<1:raise ValueError('max_length must be a positive integer')
    if not isinstance(forbidden_target_ids,(set,frozenset,list,tuple)) or any(type(x) is not int or x<0 for x in forbidden_target_ids):
        raise ValueError('forbidden_target_ids must contain nonnegative integer IDs')
    if len(full_ids)>max_length:raise ValueError('Complete example exceeds token budget; truncation is forbidden')
    if len(full_ids)<=len(prompt_ids) or full_ids[:len(prompt_ids)]!=prompt_ids:
        raise ValueError('Native prompt is not an exact prefix with a nonempty assistant suffix')
    target=full_ids[len(prompt_ids):]
    if set(target).intersection(forbidden_target_ids):raise ValueError('Assistant target contains forbidden image/video/control token IDs')
    return [-100]*len(prompt_ids)+target


def pad_supervised_batch(examples, *, pad_token_id, max_length, pad_to_multiple_of=1):
    """Right-pad IDs and labels without silently discarding supervised tokens.

    This is text-loss bookkeeping only. Native vision tensors/grids still need
    their model-specific collator and measured runtime verification.
    """
    if type(pad_token_id) is not int or pad_token_id<0:raise ValueError('Invalid pad token ID')
    if type(max_length) is not int or max_length<1:raise ValueError('Invalid maximum length')
    if type(pad_to_multiple_of) is not int or pad_to_multiple_of<1:raise ValueError('Invalid padding multiple')
    if not isinstance(examples,list) or not examples:raise ValueError('A nonempty example list is required')
    for example in examples:
        if not isinstance(example,dict):raise ValueError('Each example must be an object')
        ids=example.get('input_ids');labels=example.get('labels');_ids(ids,'input_ids')
        if not isinstance(labels,list) or len(labels)!=len(ids) or any(type(x) is not int or x not in (-100,token) for x,token in zip(labels,ids)):
            raise ValueError('Labels must match token IDs or the -100 ignore index')
        if labels[0]!=-100:raise ValueError('The first position cannot be a causal next-token target')
        if all(x==-100 for x in labels[1:]):raise ValueError('Every example must retain effective causal target tokens')
    length=max(len(e['input_ids']) for e in examples)
    length=((length+pad_to_multiple_of-1)//pad_to_multiple_of)*pad_to_multiple_of
    if length>max_length:raise ValueError('Padded batch exceeds explicit token budget')
    return {'input_ids':[e['input_ids']+[pad_token_id]*(length-len(e['input_ids'])) for e in examples],
            'labels':[e['labels']+[-100]*(length-len(e['labels'])) for e in examples],
            'attention_mask':[[1]*len(e['input_ids'])+[0]*(length-len(e['input_ids'])) for e in examples],
            'supervised_tokens':sum(x!=-100 for e in examples for x in e['labels'])}
