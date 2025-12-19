#!/usr/bin/env python3
import yaml
import subprocess
import argparse
import os

#TODO --> add parameter --> if deploy_large_job --> only consider large job
#                           if deploy_small_job --> only consider .infer
#                           if deploy_critical_job --> only consider .critical
#                           deploy_critical_job+deploy_small_job,deploy_large_job+deploy_critical_job
 
def get_num_gpus():
    try:
        output = subprocess.check_output(['nvidia-smi', '-L']).decode('utf-8')
        num_gpus = len([line for line in output.strip().split('\n') if line.strip()])
        return num_gpus
    except Exception:
        print("No NVIDIA GPUs found or nvidia-smi not installed.")
        return 0

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deploy_large_job', action='store_true')
    parser.add_argument('--deploy_small_job', action='store_true')
    parser.add_argument('--deploy_critical_job', action='store_true')
    return parser.parse_args()

def filter_values(value, args):
    items = value.split(',')

    if not (args.deploy_large_job or args.deploy_small_job or args.deploy_critical_job):
        return value  # no flag → all

    result = []
    for i in items:
        if args.deploy_large_job and i.startswith('large'):
            result.append(i)
        elif args.deploy_critical_job and 'critical' in i:
            result.append(i)
        elif args.deploy_small_job and ('infer' in i and 'large' not in i and 'critical' not in i):
            result.append(i)

    return ','.join(result)


def generate_compose(num_gpus,args):
    services = {}

    services['watchtower'] = {
    'image': 'containrrr/watchtower',
    'volumes': [
        '/var/run/docker.sock:/var/run/docker.sock',
        '~/.docker/config.json:/config.json'
    ],
    'environment': {
        'WATCHTOWER_NOTIFICATION_REPORT': 'true',
        'WATCHTOWER_NOTIFICATION_URL': 'slack://watchtower@T02DZT0TD27/B07RLPDKETB/tQo477Wsc48pXcSbkrf9qiRA',
        'WATCHTOWER_NOTIFICATION_TEMPLATE': "{{- if .Report -}}\n    \
                \        {{- with .Report -}}\n            {{len .Scanned}}\
                \ Scanned, {{len .Updated}} Updated, {{len .Failed}} Failed\n\
                \            {{- range .Updated}}\n            - {{.Name}}\
                \ ({{.ImageName}}): {{.CurrentImageID.ShortID}} updated\
                \ to {{.LatestImageID.ShortID}}\n            {{- end -}}\n\
                \            {{- range .Fresh}}\n            - {{.Name}}\
                \ ({{.ImageName}}): {{.State}}\n            {{- end -}}\n\
                \            {{- range .Skipped}}\n            - {{.Name}}\
                \ ({{.ImageName}}): {{.State}}: {{.Error}}\n           \
                \ {{- end -}}\n            {{- range .Failed}}\n       \
                \     - {{.Name}} ({{.ImageName}}): {{.State}}: {{.Error}}\n\
                \            {{- end -}}\n            {{- end -}}\n    \
                \        {{- else -}}\n            {{range .Entries -}}{{.Message}}{{\"\
                \\n\"}}{{- end -}}\n            {{- end -}}"
                }
            }
      
    worker_templates = [
        {
            'name': 'model_processor',
            'image': 'amaranth2021/model_processor:v1',
            'command': 'bash -c "celery -A main worker -l info -Q erpr_grading_pipeline_critical,erpr_grading_pipeline,large_erpr_grading_pipeline,brca_grading_pipeline_critical,brca_grading_pipeline,large_brca_grading_pipeline,her2_grading_pipeline_critical,her2_grading_pipeline,large_her2_grading_pipeline,unet_pipeline_critical,unet_pipeline,large_unet_pipeline,yolo_pipeline_critical,yolo_pipeline,large_yolo_pipeline,detr_pipeline_critical,detr_pipeline,large_detr_pipeline,dino_pipeline_critical,dino_pipeline,large_dino_pipeline,gen_annot_pipeline_critical,gen_annot_pipeline,large_gen_annot_pipeline,ki67_grading_pipeline_critical,ki67_grading_pipeline,large_ki67_grading_pipeline,unet_gpu_worker_critical,unet_gpu_worker,large_unet_gpu_worker,dino_gpu_worker_critical,dino_gpu_worker,large_dino_gpu_worker,yolo_gpu_worker_critical,yolo_gpu_worker,large_yolo_gpu_worker,detr_gpu_worker_critical,detr_gpu_worker,large_detr_gpu_worker,unet_mask,cog_analysis,flourescense_tiff,compare_layer -E -n model_processor@%h --concurrency 1 --prefetch-multiplier 1"',
            'env': {
                "celery_key_her2": "her2.critical.infer,her2.infer,large.her2.infer",
                "celery_queue_her2": "her2_grading_pipeline_critical,her2_grading_pipeline,large_her2_grading_pipeline",

                "celery_key_brca": "brca.critical.infer,brca.infer,large.brca.infer",
                "celery_queue_brca": "brca_grading_pipeline_critical,brca_grading_pipeline,large_brca_grading_pipeline",

                "celery_key_erpr": "erpr.critical.infer,erpr.infer,large.erpr.infer",
                "celery_queue_erpr": "erpr_grading_pipeline_critical,erpr_grading_pipeline,large_erpr_grading_pipeline",

                "celery_key_unet": "unet.critical.infer,unet.infer,large.unet.infer",
                "celery_queue_unet": "unet_pipeline_critical,unet_pipeline,large_unet_pipeline",

                "celery_key_yolo": "yolo.critical.infer,yolo.infer,large.yolo.infer",
                "celery_queue_yolo": "yolo_pipeline_critical,yolo_pipeline,large_yolo_pipeline",

                "celery_key_detr": "detr.critical.infer,detr.infer,large.detr.infer",
                "celery_queue_detr": "detr_pipeline_critical,detr_pipeline,large_detr_pipeline",

                "celery_key_dino": "dino.critical.infer,dino.infer,large.dino.infer",
                "celery_queue_dino": "dino_pipeline_critical,dino_pipeline,large_dino_pipeline",

                "celery_key_gen_annot": "gen_annot.critical.infer,gen_annot.infer,large.gen_annot.infer",
                "celery_queue_gen_annot": "gen_annot_pipeline_critical,gen_annot_pipeline,large_gen_annot_pipeline",

                "celery_queue_ki67": "ki67_grading_pipeline_critical,ki67_grading_pipeline,large_ki67_grading_pipeline",
                "celery_key_ki67": "ki67.critical.infer,ki67.infer,large.ki67.infer",

                "CELERY_QUEUE_UNET_GPU_WORKER": "unet_gpu_worker_critical,unet_gpu_worker,large_unet_gpu_worker",
                "CELERY_KEY_UNET_GPU_WORKER": "unet.gpu.worker.critical,unet.gpu.worker,large.unet.gpu.worker",

                "CELERY_QUEUE_DINO_GPU_WORKER": "dino_gpu_worker_critical,dino_gpu_worker,large_dino_gpu_worker",
                "CELERY_KEY_DINO_GPU_WORKER": "dino.gpu.worker.critical,dino.gpu.worker,large.dino.gpu.worker",

                "CELERY_QUEUE_YOLO_GPU_WORKER": "yolo_gpu_worker_critical,yolo_gpu_worker,large_yolo_gpu_worker",
                "CELERY_KEY_YOLO_GPU_WORKER": "yolo.gpu.worker.critical,yolo.gpu.worker,large.yolo.gpu.worker",

                "CELERY_QUEUE_DETR_GPU_WORKER": "detr_gpu_worker_critical,detr_gpu_worker,large_detr_gpu_worker",
                "CELERY_KEY_DETR_GPU_WORKER": "detr.gpu.worker.critical,detr.gpu.worker,large.detr.gpu.worker",

                "CELERY_KEY_UNET_MASK_IMG": "unet.mask.infer",
                "CELERY_QUEUE_MASK_IMG": "unet_mask",

                'environment': 'prod-secrets',
                'batch_size': 16,
                'NVIDIA_DEVICE': 0,
                "VAULT_ADDR": os.getenv("VAULT_ADDRESS"),
                "VAULT_TOKEN": os.getenv("VAULT_TOKEN")
            },
            'shm_size': '10gb'
        },
        {
            'name': 'yolo_worker',
            'image': 'amaranth2021/yolo-worker:latest',
            'command': 'bash -c "celery -A main worker -l info -Q yolo_gpu_worker,large_yolo_gpu_worker,yolo_gpu_worker_critical -E -n yolo_worker@%h --concurrency=1"',
            'env': {
                'CELERY_KEY': 'yolo.gpu.worker,large.yolo.gpu.worker,yolo.gpu.worker.critical',
                'CELERY_QUEUE': 'yolo_gpu_worker,large_yolo_gpu_worker,yolo_gpu_worker_critical',
                'VAULT_ADDR': os.getenv("VAULT_ADDRESS"),
                'VAULT_TOKEN': os.getenv("VAULT_TOKEN"),
                'NVIDIA_DEVICE': 0
            }
        },
        {
            'name': 'unet_worker',
            'image': 'amaranth2021/unet-worker:latest',
            'command': 'bash -c "celery -A main worker -l info -Q unet_gpu_worker,large_unet_gpu_worker,unet_gpu_worker_critical,unet_mask,patient_analysis -E -n unet_worker@%h --concurrency=1"',
            'env': {
                'CELERY_KEY': 'unet.gpu.worker,large.unet.gpu.worker,unet.gpu.worker.critical',
                'CELERY_QUEUE': 'unet_gpu_worker,large_unet_gpu_worker,unet_gpu_worker_critical',
                'VAULT_ADDR': os.getenv("VAULT_ADDRESS"),
                'VAULT_TOKEN': os.getenv("VAULT_TOKEN"),
                'NVIDIA_DEVICE': 0
            }
        },
        {
            'name': 'dino_worker',
            'image': 'amaranth2021/dino-worker:latest',
            'command': 'bash -c "celery -A main worker -l info -Q dino_gpu_worker,large_dino_gpu_worker,dino_gpu_worker_critical -E -n dino_worker@%h --concurrency=1"',
            'env': {
                'CELERY_KEY': 'dino.gpu.worker,large.dino.gpu.worker,dino.gpu.worker.critical',
                'CELERY_QUEUE': 'dino_gpu_worker,large_dino_gpu_worker,dino_gpu_worker_critical',
                'VAULT_ADDR': os.getenv("VAULT_ADDRESS"),
                'VAULT_TOKEN': os.getenv("VAULT_TOKEN"),
                'NVIDIA_DEVICE': 0
            }
        },
        {
            'name': 'detr_worker',
            'image': 'amaranth2021/detr-worker:latest',
            'command': 'bash -c "celery -A main worker -l info -Q detr_gpu_worker,large_detr_gpu_worker,detr_gpu_worker_critical -E -n detr_worker@%h --concurrency=1"',
            'env': {
                'CELERY_KEY': 'detr.gpu.worker,large.detr.gpu.worker,detr.gpu.worker.critical',
                'CELERY_QUEUE': 'detr_gpu_worker,large_detr_gpu_worker,detr_gpu_worker_critical',
                'VAULT_ADDR': os.getenv("VAULT_ADDRESS"),
                'VAULT_TOKEN': os.getenv("VAULT_TOKEN"),
                'NVIDIA_DEVICE': 0
            }
        }
    ]
    for template in worker_templates:
        for i in range(num_gpus):
            service_name = f"{template['name']}{i+1}" if num_gpus > 1 else template['name']
            env = template['env'].copy()
            if 'NVIDIA_DEVICE' in env:
                env['NVIDIA_DEVICE'] = int(i)

            for k, v in env.items():
                if 'queue' in k.lower() or 'key' in k.lower():
                    env[k] = filter_values(v, args)   

            service_def = {
                'container_name': service_name,
                'image': template['image'],
                "privileged": False,
                'runtime': 'nvidia',
                'network_mode': 'host',
                'security_opt': ['apparmor=unconfined'],
                'restart': 'on-failure',
                'environment': env,
                'command': template['command']
            }
            if 'shm_size' in template:
                service_def['shm_size'] = template['shm_size']
            services[service_name] = service_def

    compose_dict = {
        'version': '3.3',
        'services': services
    }

    return compose_dict

def main():
    args = parse_args()
    num_gpus = get_num_gpus()
    # if num_gpus == 0:
    #     print("No GPUs detected, exiting.")
    #     return

    print(f"Detected {num_gpus} GPU(s). Generating docker-compose file...")

    compose_yaml = generate_compose(num_gpus, args)

    output_file = "docker-compose.yml"
    with open(output_file, 'w') as f:
        yaml.dump(compose_yaml, f, default_flow_style=False, sort_keys=False, indent=4, width=1000, allow_unicode=True)

    print(f"Docker Compose file generated: {output_file}")
    print("Applying the docker compose")
    # os.system("docker compose down")
    # os.system("docker compose up -d")
    # os.remove("docker-compose.yml")

if __name__ == "__main__":
    main()