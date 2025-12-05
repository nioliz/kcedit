# kcedit - Kubernetes Config Editor

`kcedit.py` is a command-line utility for managing kubectl configuration files (`~/.kube/config`). It provides a simple interface for common kubeconfig operations.

## Features

- ✅ **List contexts** with current context indicator
- ✅ **Import/export** contexts with associated users and clusters
- ✅ **Switch** between contexts easily
- ✅ **Safe operations** with automatic backups
- ✅ **Clean output** with informative formatting
- ✅ **Handles special characters** in user names

## Installation

1. Install Python dependency:
```bash
pip install pyyaml
```
or
```bash
apt install python3-yaml
```

2. Make the script executable:

```bash
sudo mv kcedit.py /usr/local/bin/kcedit
```

3. Usage:
  kcedit.py <command> [arguments]

Commands:
  ls <target>        List configuration elements
    context          List all contexts with format: context.name: 'user' @ 'cluster'
                     Current context marked with '*'
    users            List all user names
    cluster          List all clusters (name and server URL)
    
  import <filename> [context-name]
                     Import contexts from another kubeconfig file
                     If context-name specified, import only that context
                     Always imports associated users and clusters
                     
  export <filename> <context-name>
                     Export specific context to standalone kubeconfig file
                     Includes associated user, cluster, and sets current-context
                     
  switch <context-name>
                     Change current context to specified context

Examples:
  kcedit.py ls                        List all contexts
  kcedit.py ls users                  List all users
  kcedit.py import backup.yaml        Import all contexts from backup.yaml
  kcedit.py import backup.yaml prod   Import only 'prod' context
  kcedit.py export prod.yaml staging  Export 'staging' context to prod.yaml
  kcedit.py switch minikube           Switch to minikube context

Notes:
  - Creates automatic backup at ~/.kube/config.bak before modifications
  - Requires pyyaml Python library
  - Maintains proper file permissions (600)
