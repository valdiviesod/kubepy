import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import axios from 'axios';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';

const API_URL = 'http://192.168.1.5:5000';  // Test API IP

const Dashboard = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [pods, setPods] = useState([]);
  const [error, setError] = useState('');
  const { register, handleSubmit, reset } = useForm();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsLoggedIn(true);
      fetchPods();
    }
  }, []);

  const fetchPods = async () => {
    try {
      const response = await axios.get(`${API_URL}/pods`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setPods(response.data);
    } catch (err) {
      setError('Failed to fetch pods');
    }
  };

  const onLogin = async (data) => {
    try {
      const response = await axios.post(`${API_URL}/login`, data);
      localStorage.setItem('token', response.data.access_token);
      setIsLoggedIn(true);
      fetchPods();
    } catch (err) {
      setError('Login failed');
    }
  };

  const onRegister = async (data) => {
    try {
      await axios.post(`${API_URL}/register`, data);
      setError('Registration successful. Please login.');
    } catch (err) {
      setError('Registration failed');
    }
  };

  const onCreatePod = async (data) => {
    try {
      await axios.post(`${API_URL}/pods`, data, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      fetchPods();
    } catch (err) {
      setError('Failed to create pod');
    }
  };

  const onDeletePod = async (podName) => {
    try {
      await axios.delete(`${API_URL}/pods/${podName}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      fetchPods();
    } catch (err) {
      setError('Failed to delete pod');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setPods([]);
  };

  if (!isLoggedIn) {
    return (
      <div className="container mx-auto p-4">
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Login</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onLogin)}>
              <Input {...register('username')} placeholder="Username" className="mb-2" />
              <Input {...register('password')} type="password" placeholder="Password" className="mb-2" />
              <Button type="submit">Login</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Register</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onRegister)}>
              <Input {...register('username')} placeholder="Username" className="mb-2" />
              <Input {...register('password')} type="password" placeholder="Password" className="mb-2" />
              <Button type="submit">Register</Button>
            </form>
          </CardContent>
        </Card>

        {error && (
          <Alert className="mt-4">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <Button onClick={logout} className="mb-4">Logout</Button>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Create Pod</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onCreatePod)}>
            <Input {...register('name')} placeholder="Pod Name" className="mb-2" />
            <Input {...register('image')} placeholder="Image" className="mb-2" />
            <Button type="submit">Create Pod</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your Pods</CardTitle>
        </CardHeader>
        <CardContent>
          {pods.map((pod) => (
            <div key={pod.name} className="flex justify-between items-center mb-2">
              <span>{pod.name} - {pod.ip}</span>
              <Button onClick={() => onDeletePod(pod.name)} variant="destructive">Delete</Button>
            </div>
          ))}
        </CardContent>
      </Card>

      {error && (
        <Alert className="mt-4">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default Dashboard;