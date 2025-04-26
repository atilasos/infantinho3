{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    # Add pkgs.postgresql if you prefer it over SQLite for development
    # pkgs.postgresql
  ];

  # Sets environment variables in the workspace
  env = {};
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      # Add any VS Code extensions you recommend for Django/Python development
      "ms-python.python" 
      # "batisteo.vscode-django" # Optional Django specific extension
    ];

    # Enable previews
    previews = {
      enable = true;
      previews = {
        web = {
          # Run the Django development server
          command = ["python" "manage.py" "runserver" "0.0.0.0:$PORT"];
          manager = "web";
          # Optional: Set environment variables for the server if needed
          # env = {
          #   DJANGO_SETTINGS_MODULE = "infantinho3.settings"; # Example
          # };
        };
      };
    };

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # Install Python dependencies
        install-deps = "pip install -r requirements.txt";
        # Perform initial database migrations
        init-db = "python manage.py migrate";
        # Optional: Seed initial data if you have a script for it
        # seed-data = "python seed_script.py"; # Example
      };
      # Runs when the workspace is (re)started
      onStart = {
        # Example: remind user how to start the server (or start automatically via preview)
        # start-server-msg = "echo 'Run the web preview or start the server using: python manage.py runserver'"; 
      };
    };
  };
}
