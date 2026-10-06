"""CLI wiring for explicit experiment records and retained-hash operations."""
from pathlib import Path


def add_commands(commands):
    validate=commands.add_parser('experiment-validate',help='Validate an explicit pre-run record; optionally verify actual artifacts')
    validate.add_argument('record',type=Path);validate.add_argument('--artifact-root',type=Path)
    create=commands.add_parser('receipt-create',help='Hash selected local artifacts into a new receipt')
    create.add_argument('--artifact-root',type=Path,required=True)
    create.add_argument('--select',action='append',required=True,help='Relative file/directory; repeat for multiple selections')
    create.add_argument('--output',type=Path,required=True)
    verify=commands.add_parser('receipt-verify',help='Check selected artifact drift against an independently retained receipt hash')
    verify.add_argument('receipt',type=Path);verify.add_argument('--artifact-root',type=Path,required=True)
    verify.add_argument('--expected-sha256',required=True)
    freeze=commands.add_parser('confirmation-freeze',help='Freeze one explicit confirmation record into a new ledger')
    freeze.add_argument('record',type=Path);freeze.add_argument('--artifact-root',type=Path,required=True)
    freeze.add_argument('--store',type=Path,required=True);freeze.add_argument('--time',required=True)
    for action in ('open','result','retire','verify'):
        parser=commands.add_parser('confirmation-'+action,help='Explicit local confirmation '+action+' transition/check')
        parser.add_argument('ledger',type=Path)
        if action!='retire':parser.add_argument('--artifact-root',type=Path,required=True)
        parser.add_argument('--freeze-sha256',required=True);parser.add_argument('--latest-sha256',required=True)
        if action!='verify':parser.add_argument('--time',required=True)
        if action=='result':parser.add_argument('result_path',help='Result file relative to artifact root')
        if action=='retire':parser.add_argument('--reason',required=True)


def execute(args, load):
    from . import experiments as e
    if args.command=='experiment-validate':
        result=e.verify_experiment_record(load(args.record),args.artifact_root) if args.artifact_root else {
            'ok':True,'scope':'declaration_only_files_not_checked','record':e.validate_experiment_record(load(args.record))}
    elif args.command=='receipt-create':result=e.create_artifact_receipt(args.artifact_root,args.select,args.output)
    elif args.command=='receipt-verify':result=e.verify_artifact_receipt(args.artifact_root,load(args.receipt),expected_receipt_sha256=args.expected_sha256)
    elif args.command=='confirmation-freeze':result=e.freeze_confirmation(load(args.record),args.artifact_root,args.store,frozen_at_utc=args.time)
    else:
        anchors=dict(expected_freeze_sha256=args.freeze_sha256,expected_latest_sha256=args.latest_sha256)
        if args.command=='confirmation-open':result=e.open_confirmation(args.ledger,args.artifact_root,opened_at_utc=args.time,**anchors)
        elif args.command=='confirmation-result':result=e.record_confirmation_result(args.ledger,args.artifact_root,args.result_path,recorded_at_utc=args.time,**anchors)
        elif args.command=='confirmation-retire':result=e.retire_confirmation(args.ledger,reason=args.reason,retired_at_utc=args.time,**anchors)
        elif args.command=='confirmation-verify':result=e.verify_confirmation(args.ledger,args.artifact_root,**anchors)
        else:raise ValueError('Unknown experiment command')
    return result,0 if result.get('ok',True) else 2
